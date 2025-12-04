"""Agentic RAG workflow using LangGraph (Corrective RAG pattern)."""

import hashlib
from typing import List, TypedDict, Annotated, Any, Dict

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from research_agent.infrastructure.vector_store.langchain_pgvector import PGVectorRetriever
from research_agent.shared.utils.logger import logger

# Query rewrite cache (in-memory, simple LRU could be added later)
_rewrite_cache: Dict[str, Dict[str, str]] = {}


# --- Logging Callback Handler ---

class LoggingCallbackHandler(BaseCallbackHandler):
    """Callback handler for logging LLM calls."""
    
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Log when LLM starts."""
        model = "unknown"
        if serialized:
            model = serialized.get("kwargs", {}).get("model_name", "unknown")
        logger.info(f"[LLM] Starting call to {model}")
        for i, prompt in enumerate(prompts):
            # Truncate long prompts
            truncated = prompt[:300] + "..." if len(prompt) > 300 else prompt
            logger.debug(f"[LLM] Prompt {i}: {truncated}")
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Log when LLM ends."""
        if response and response.generations:
            for i, gen in enumerate(response.generations):
                for j, g in enumerate(gen):
                    content = g.text[:500] + "..." if len(g.text) > 500 else g.text
                    logger.info(f"[LLM] Raw response: {content}")
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Log LLM errors."""
        logger.error(f"[LLM] Error: {error}")
    
    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Log when chain starts."""
        chain_name = "unknown"
        if serialized:
            chain_name = serialized.get("name") or serialized.get("id", ["unknown"])[-1] if serialized.get("id") else "unknown"
        logger.debug(f"[Chain] Starting: {chain_name}")
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Log when chain ends."""
        logger.debug(f"[Chain] Completed")
    
    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Log chain errors."""
        logger.error(f"[Chain] Error: {error}")


# Create default callback handler
logging_callback = LoggingCallbackHandler()


# --- State Schema ---

class GraphState(TypedDict):
    """State for the RAG graph."""
    question: str  # Original user question
    rewritten_question: str  # Rewritten question with context
    chat_history: List[tuple[str, str]]  # List of (human, ai) message tuples
    documents: List[Document]  # Retrieved documents
    reranked_documents: List[Document]  # Reranked documents
    generation: str  # Final answer
    filtered_documents: List[Document]  # Filtered relevant documents


# --- Grading Schema ---

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


# --- Helper Functions for Query Rewriting ---

def needs_rewriting(question: str, chat_history: List[tuple[str, str]]) -> bool:
    """
    Smart check if query rewriting is actually needed.
    
    Returns True if:
    - Question contains pronouns/references (it, that, them, this, etc.)
    - Question is very short (< 10 chars) and has history
    - Question contains context-dependent words
    """
    if not chat_history:
        return False
    
    question_lower = question.lower()
    
    # Check for pronouns and references
    pronouns = ["it", "that", "them", "this", "these", "those", "he", "she", "they", "his", "her", "their"]
    if any(pronoun in question_lower for pronoun in pronouns):
        return True
    
    # Very short questions with history likely need context
    if len(question.strip()) < 10:
        return True
    
    # Context-dependent words
    context_words = ["also", "again", "more", "another", "same", "different", "previous", "earlier"]
    if any(word in question_lower for word in context_words):
        return True
    
    return False


def get_cache_key(question: str, chat_history: List[tuple[str, str]]) -> str:
    """Generate cache key from question and recent history."""
    # Use last 3 turns for cache key
    recent_history = chat_history[-3:] if chat_history else []
    history_str = "|".join([f"{h[0]}:{h[1]}" for h in recent_history])
    key_str = f"{question}|{history_str}"
    return hashlib.md5(key_str.encode()).hexdigest()


def validate_rewrite(original: str, rewritten: str, max_expansion_ratio: float = 3.0) -> bool:
    """
    Validate rewrite quality.
    
    Returns False if:
    - Rewritten is too long compared to original (expansion ratio exceeded)
    - Rewritten is empty or too short
    - Rewritten is identical to original (no improvement)
    """
    if not rewritten or len(rewritten.strip()) < 3:
        logger.warning("Rewrite too short or empty")
        return False
    
    if rewritten.strip() == original.strip():
        logger.warning("Rewrite identical to original")
        return False
    
    # Check expansion ratio
    original_len = len(original)
    rewritten_len = len(rewritten)
    
    if original_len > 0:
        expansion_ratio = rewritten_len / original_len
        if expansion_ratio > max_expansion_ratio:
            logger.warning(f"Rewrite too long: {expansion_ratio:.2f}x expansion (max {max_expansion_ratio})")
            return False
    
    return True


# --- Node Functions ---

async def transform_query(
    state: GraphState,
    llm: ChatOpenAI,
    enable_validation: bool = True,
    enable_cache: bool = True,
    max_expansion_ratio: float = 3.0
) -> GraphState:
    """
    Enhanced query rewriting with validation and optimization.
    
    Args:
        state: Graph state containing question and chat_history
        llm: Language model for rewriting
        enable_validation: Validate rewrite quality before using
        enable_cache: Cache rewrite results
        max_expansion_ratio: Maximum allowed expansion ratio (rewritten/original length)
    """
    question = state["question"]
    chat_history = state.get("chat_history", [])
    
    # Quick return if no history
    if not chat_history:
        logger.info("No chat history, using original question")
        return {"rewritten_question": question, "question": question}
    
    # Smart skip: check if rewriting is actually needed
    if not needs_rewriting(question, chat_history):
        logger.info("Query doesn't need rewriting")
        return {"rewritten_question": question, "question": question}
    
    # Check cache
    cache_key = None
    if enable_cache:
        cache_key = get_cache_key(question, chat_history)
        if cache_key in _rewrite_cache:
            logger.info("Cache hit for query rewrite")
            return _rewrite_cache[cache_key]
    
    logger.info(f"Rewriting query with {len(chat_history)} history messages")
    
    # Build context
    history_context = "\n".join([
        f"Human: {human}\nAssistant: {ai}"
        for human, ai in chat_history[-3:]  # Use last 3 turns
    ])
    
    # Improved prompt with examples
    system_prompt = """You are a query rewriting assistant. Rewrite the user's question to be standalone.

Rules:
1. Resolve pronouns (it, that, them, etc.) with their actual referents
2. Include ONLY essential context from history
3. DO NOT add details the user didn't mention
4. Keep the question's original scope and openness
5. Output ONLY the rewritten question

Examples:
History: "什么是图谱模式" -> "图谱模式是..."
Question: "如何定义它？"
Rewrite: "如何定义图谱模式？" ✓
NOT: "如何通过配置文件定义图谱模式的Node对象？" ✗"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "History:\n{history}\n\nQuestion: {question}\n\nRewrite:"),
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        rewritten = chain.invoke(
            {"history": history_context, "question": question},
            config={"callbacks": [logging_callback]}
        )
        rewritten = rewritten.strip()
        
        # Validate rewrite quality
        if enable_validation and not validate_rewrite(question, rewritten, max_expansion_ratio):
            logger.warning("Validation failed, using original")
            rewritten = question
        
        logger.info(f"[Rewrite] '{question}' -> '{rewritten}'")
        
        result = {"rewritten_question": rewritten, "question": question}
        
        # Cache result
        if enable_cache and cache_key:
            _rewrite_cache[cache_key] = result
            # Simple cache size limit (keep last 100 entries)
            if len(_rewrite_cache) > 100:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(_rewrite_cache))
                del _rewrite_cache[oldest_key]
        
        return result
        
    except Exception as e:
        logger.error(f"Rewrite failed: {e}")
        return {"rewritten_question": question, "question": question}


async def retrieve(state: GraphState, retriever: PGVectorRetriever) -> GraphState:
    """Retrieve documents from vector store using rewritten query."""
    # Use rewritten question if available, otherwise use original
    query = state.get("rewritten_question", state["question"])
    logger.info(f"Retrieving documents for query: {query}")
    
    # Async retriever call
    documents = await retriever._aget_relevant_documents(query)
    
    logger.info(f"Retrieved {len(documents)} documents")
    return {"documents": documents}


async def rerank(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """
    Rerank retrieved documents using LLM-based relevance scoring.
    Takes top-k documents and reranks them for better precision.
    """
    question = state.get("rewritten_question", state["question"])
    documents = state["documents"]
    
    if not documents:
        logger.warning("No documents to rerank")
        return {"reranked_documents": []}
    
    logger.info(f"Reranking {len(documents)} documents")
    
    # Prompt for scoring document relevance
    system_prompt = """You are a document relevance scorer. Rate how relevant the given document 
is to answering the user's question on a scale of 0-10.

0 = Completely irrelevant
5 = Somewhat relevant
10 = Highly relevant and directly answers the question

Output ONLY a single number between 0-10. No explanation."""
    
    score_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Question: {question}\n\nDocument: {document}\n\nRelevance score (0-10):"),
    ])
    
    chain = score_prompt | llm | StrOutputParser()
    
    # Score each document
    doc_scores = []
    for i, doc in enumerate(documents):
        try:
            # Truncate very long documents
            doc_content = doc.page_content[:2000] if len(doc.page_content) > 2000 else doc.page_content
            
            result = chain.invoke(
                {"question": question, "document": doc_content},
                config={"callbacks": [logging_callback]}
            )
            
            # Parse score
            try:
                score = float(result.strip().split()[0])  # Get first number
                score = max(0.0, min(10.0, score))  # Clamp to 0-10
            except (ValueError, IndexError):
                logger.warning(f"[Rerank] Failed to parse score from '{result}', using 5.0")
                score = 5.0
            
            doc_scores.append((score, doc))
            logger.debug(f"[Rerank] Doc {i+1}: score={score}")
        except Exception as e:
            logger.warning(f"[Rerank] Error scoring doc {i+1}: {e}")
            doc_scores.append((5.0, doc))  # Default mid-score
    
    # Sort by score (descending) and take top documents
    sorted_docs = sorted(doc_scores, key=lambda x: x[0], reverse=True)
    reranked = [doc for score, doc in sorted_docs if score >= 5.0]  # Filter low scores
    
    logger.info(f"Reranking complete: {len(reranked)}/{len(documents)} docs passed (score >= 5)")
    return {"reranked_documents": reranked}


def grade_documents(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """Grade retrieved documents for relevance."""
    # Defensive check for required fields
    if "question" not in state and "rewritten_question" not in state:
        logger.error(f"[Grade] Missing 'question' in state. Available keys: {list(state.keys())}")
        raise ValueError("State must contain 'question' or 'rewritten_question' field")
    
    question = state.get("rewritten_question", state.get("question", ""))
    # Use reranked documents if available, otherwise use retrieved documents
    documents = state.get("reranked_documents", state.get("documents", []))
    logger.info(f"[Grade] Grading {len(documents)} documents for relevance (question: '{question[:50]}...')")
    
    # Simple prompt that asks for yes/no directly (no structured output needed)
    system_prompt = """You are a grader assessing relevance of a retrieved document to a user question.
If the document contains keyword(s) or semantic meaning related to the question, it is relevant.
Reply with ONLY 'yes' or 'no'. Nothing else."""
    
    grade_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Document: {document}\n\nQuestion: {question}\n\nIs this document relevant? Reply only 'yes' or 'no':"),
    ])
    
    chain = grade_prompt | llm | StrOutputParser()
    
    # Grade each document
    filtered_docs = []
    for i, doc in enumerate(documents):
        try:
            logger.debug(f"[Grade] Grading document {i+1}/{len(documents)}")
            
            # Truncate very long documents
            doc_content = doc.page_content[:2000] if len(doc.page_content) > 2000 else doc.page_content
            
            result = chain.invoke(
                {"question": question, "document": doc_content},
                config={"callbacks": [logging_callback]}
            )
            
            # Parse the response - look for yes/no
            result_lower = result.strip().lower()
            logger.info(f"[Grade] Document {i+1} raw response: '{result_lower}'")
            
            is_relevant = "yes" in result_lower and "no" not in result_lower[:10]
            logger.info(f"[Grade] Document {i+1} relevant: {is_relevant} (metadata: {doc.metadata})")
            
            if is_relevant:
                filtered_docs.append(doc)
        except Exception as e:
            import traceback
            logger.warning(
                f"[Grade] Failed to grade document {i+1}: {type(e).__name__}: {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            # On error, include the document (fail-safe: better to include than exclude)
            filtered_docs.append(doc)
    
    logger.info(f"Grading complete. {len(filtered_docs)}/{len(documents)} documents passed")
    return {"filtered_documents": filtered_docs}


def generate(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """Generate answer from filtered documents."""
    # Use original question for generation
    question = state["question"]
    documents = state.get("filtered_documents", state.get("reranked_documents", state.get("documents", [])))
    
    logger.info(f"Generating answer using {len(documents)} documents")
    
    # Check if we have documents
    if not documents:
        logger.warning("No relevant documents found for generation")
        return {
            "generation": "I don't have enough relevant information in the documents to answer this question.",
        }
    
    # Build context from documents
    context = "\n\n".join([doc.page_content for doc in documents])
    logger.debug(f"[Generate] Context length: {len(context)} chars")
    
    # Prompt
    system_prompt = """You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Question: {question}\n\nContext: {context}\n\nAnswer:"),
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        generation = chain.invoke(
            {"question": question, "context": context},
            config={"callbacks": [logging_callback]}
        )
        logger.info(f"[Generate] Response generated: {len(generation)} chars")
    except Exception as e:
        logger.error(f"[Generate] Failed to generate response: {e}")
        generation = "I encountered an error while generating the response. Please try again."
    
    return {"generation": generation}


# --- Graph Builder ---

def create_rag_graph(
    retriever: PGVectorRetriever,
    llm: ChatOpenAI,
    use_rewrite: bool = True,
    use_rerank: bool = True,
    use_grading: bool = True,
    enable_rewrite_validation: bool = True,
    enable_rewrite_cache: bool = True,
    max_expansion_ratio: float = 3.0,
) -> StateGraph:
    """
    Create the Enhanced Agentic RAG graph.
    
    Flow (all nodes enabled):
    1. Transform Query - Rewrite query with chat history context
    2. Retrieve - Get documents from vector store (with optional hybrid search)
    3. Rerank - LLM-based relevance scoring
    4. Grade Documents - Binary relevance check
    5. Generate - Create final answer
    
    Args:
        retriever: PGVector retriever (can use hybrid search)
        llm: Language model for rewriting, reranking, grading, and generation
        use_rewrite: Enable query rewriting with chat history
        use_rerank: Enable LLM-based reranking
        use_grading: Enable binary relevance grading
        enable_rewrite_validation: Validate rewrite quality before using
        enable_rewrite_cache: Cache rewrite results to avoid redundant LLM calls
        max_expansion_ratio: Maximum allowed expansion ratio (rewritten/original length)
    """
    workflow = StateGraph(GraphState)
    
    # Add nodes based on configuration
    if use_rewrite:
        # Create wrapper function with validation and cache settings
        async def transform_query_wrapper(state: GraphState) -> GraphState:
            return await transform_query(
                state, llm,
                enable_validation=enable_rewrite_validation,
                enable_cache=enable_rewrite_cache,
                max_expansion_ratio=max_expansion_ratio,
            )
        workflow.add_node("transform_query", transform_query_wrapper)
    
    workflow.add_node("retrieve", lambda state: retrieve(state, retriever))
    
    if use_rerank:
        workflow.add_node("rerank", lambda state: rerank(state, llm))
    
    if use_grading:
        workflow.add_node("grade_documents", lambda state: grade_documents(state, llm))
    
    workflow.add_node("generate", lambda state: generate(state, llm))
    
    # Build graph edges
    if use_rewrite:
        workflow.set_entry_point("transform_query")
        workflow.add_edge("transform_query", "retrieve")
    else:
        workflow.set_entry_point("retrieve")
    
    if use_rerank:
        workflow.add_edge("retrieve", "rerank")
        if use_grading:
            workflow.add_edge("rerank", "grade_documents")
            workflow.add_edge("grade_documents", "generate")
        else:
            workflow.add_edge("rerank", "generate")
    else:
        if use_grading:
            workflow.add_edge("retrieve", "grade_documents")
            workflow.add_edge("grade_documents", "generate")
        else:
            workflow.add_edge("retrieve", "generate")
    
    workflow.add_edge("generate", END)
    
    return workflow.compile()


# --- Streaming Support ---

async def stream_rag_response(
    question: str,
    retriever: PGVectorRetriever,
    llm: ChatOpenAI,
    chat_history: List[tuple[str, str]] = None,
    use_rewrite: bool = True,
    use_rerank: bool = True,
    use_grading: bool = True,
    enable_rewrite_validation: bool = True,
    enable_rewrite_cache: bool = True,
    max_expansion_ratio: float = 3.0,
):
    """
    Stream RAG response token by token with enhanced pipeline.
    
    Args:
        question: User question
        retriever: PGVector retriever
        llm: Language model
        chat_history: List of (human, ai) message tuples
        use_rewrite: Enable query rewriting
        use_rerank: Enable reranking
        use_grading: Enable grading
        enable_rewrite_validation: Validate rewrite quality before using
        enable_rewrite_cache: Cache rewrite results to avoid redundant LLM calls
        max_expansion_ratio: Maximum allowed expansion ratio (rewritten/original length)
    
    Yields:
        dict with 'type' and 'content' keys
    """
    logger.info(f"[Stream] Starting enhanced RAG stream for: {question[:50]}...")
    
    # Initialize state
    state = {
        "question": question,
        "chat_history": chat_history or [],
    }
    
    # Step 1: Query rewriting (optional)
    if use_rewrite and chat_history:
        logger.info("[Stream] Rewriting query...")
        rewrite_result = await transform_query(
            state, llm,
            enable_validation=enable_rewrite_validation,
            enable_cache=enable_rewrite_cache,
            max_expansion_ratio=max_expansion_ratio,
        )
        state.update(rewrite_result)  # Merge instead of replace
    else:
        state["rewritten_question"] = question
    
    # Step 2: Retrieve documents
    retrieve_result = await retrieve(state, retriever)
    state.update(retrieve_result)  # Merge instead of replace
    yield {"type": "sources", "documents": state["documents"]}
    
    # Step 3: Rerank (optional)
    if use_rerank:
        logger.info("[Stream] Reranking documents...")
        rerank_result = await rerank(state, llm)
        state.update(rerank_result)  # Merge instead of replace
        documents = state.get("reranked_documents", [])
    else:
        documents = state.get("documents", [])
    
    # Step 4: Grade documents (optional)
    if use_grading:
        logger.info("[Stream] Grading documents...")
        state["reranked_documents"] = documents  # Pass to grading
        logger.debug(f"[Stream] State keys before grading: {list(state.keys())}")
        grade_result = grade_documents(state, llm)
        state.update(grade_result)  # Merge instead of replace
        documents = state.get("filtered_documents", [])
    
    filtered_count = len(documents)
    logger.info(f"[Stream] {filtered_count} documents for generation")
    
    if filtered_count == 0:
        logger.warning("[Stream] No relevant documents found")
        yield {"type": "token", "content": "I don't have enough relevant information to answer this question."}
        yield {"type": "done"}
        return
    
    # Stream generation
    context = "\n\n".join([doc.page_content for doc in documents])
    logger.info(f"[Stream] Generating response with {len(context)} chars context")
    
    system_prompt = """You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Question: {question}\n\nContext: {context}\n\nAnswer:"),
    ])
    
    # Create streaming LLM with callback
    streaming_llm = llm.with_config({"streaming": True, "callbacks": [logging_callback]})
    chain = prompt | streaming_llm | StrOutputParser()
    
    # Stream tokens
    token_count = 0
    try:
        async for token in chain.astream({"question": question, "context": context}):
            token_count += 1
            yield {"type": "token", "content": token}
        logger.info(f"[Stream] Generation complete: {token_count} tokens")
    except Exception as e:
        import traceback
        logger.error(
            f"[Stream] Generation error: {type(e).__name__}: {e}\n"
            f"Question: {question[:100]}...\n"
            f"Context length: {len(context)} chars\n"
            f"Traceback:\n{traceback.format_exc()}",
            exc_info=True
        )
        yield {"type": "token", "content": f"\n\n[Error: {type(e).__name__}: {str(e)}]"}
    
    yield {"type": "done"}

