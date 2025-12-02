"""Agentic RAG workflow using LangGraph (Corrective RAG pattern)."""

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


# --- Node Functions ---

async def transform_query(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """
    Rewrite the query with chat history context for better retrieval.
    Handles coreference resolution (e.g., "it", "that", "them").
    """
    question = state["question"]
    chat_history = state.get("chat_history", [])
    
    # If no chat history, return original question
    if not chat_history:
        logger.info("No chat history, using original question")
        return {"rewritten_question": question, "question": question}
    
    logger.info(f"Rewriting query with {len(chat_history)} history messages")
    
    # Build context from chat history
    history_context = "\n".join([
        f"Human: {human}\nAssistant: {ai}"
        for human, ai in chat_history[-3:]  # Use last 3 turns
    ])
    
    # Prompt for query rewriting
    system_prompt = """You are a query rewriting assistant. Your task is to rewrite the user's latest question 
to be a standalone question that includes necessary context from the conversation history.

Rules:
1. Resolve all pronouns and references (it, that, them, this, etc.)
2. Include relevant context from previous messages
3. Keep the question concise and focused
4. Maintain the original intent
5. Output ONLY the rewritten question, nothing else."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Conversation history:\n{history}\n\nLatest question: {question}\n\nRewritten question:"),
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        rewritten = chain.invoke(
            {"history": history_context, "question": question},
            config={"callbacks": [logging_callback]}
        )
        logger.info(f"[Rewrite] Original: '{question}' -> Rewritten: '{rewritten}'")
        return {"rewritten_question": rewritten.strip(), "question": question}
    except Exception as e:
        logger.error(f"[Rewrite] Failed: {e}")
        # Fallback to original question
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
    question = state.get("rewritten_question", state["question"])
    # Use reranked documents if available, otherwise use retrieved documents
    documents = state.get("reranked_documents", state.get("documents", []))
    logger.info(f"Grading {len(documents)} documents for relevance")
    
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
            logger.debug(f"[Grade] Document {i+1} relevant: {is_relevant}")
            
            if is_relevant:
                filtered_docs.append(doc)
        except Exception as e:
            logger.warning(f"[Grade] Failed to grade document {i+1}: {e}")
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
    """
    workflow = StateGraph(GraphState)
    
    # Add nodes based on configuration
    if use_rewrite:
        workflow.add_node("transform_query", lambda state: transform_query(state, llm))
    
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
        state = await transform_query(state, llm)
    else:
        state["rewritten_question"] = question
    
    # Step 2: Retrieve documents
    state = await retrieve(state, retriever)
    yield {"type": "sources", "documents": state["documents"]}
    
    # Step 3: Rerank (optional)
    if use_rerank:
        logger.info("[Stream] Reranking documents...")
        state = await rerank(state, llm)
        documents = state.get("reranked_documents", [])
    else:
        documents = state.get("documents", [])
    
    # Step 4: Grade documents (optional)
    if use_grading:
        logger.info("[Stream] Grading documents...")
        state["reranked_documents"] = documents  # Pass to grading
        state = grade_documents(state, llm)
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
        logger.error(f"[Stream] Generation error: {e}")
        yield {"type": "token", "content": f"\n\n[Error: {str(e)}]"}
    
    yield {"type": "done"}

