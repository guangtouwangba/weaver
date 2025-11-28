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
    question: str
    documents: List[Document]
    generation: str
    filtered_documents: List[Document]


# --- Grading Schema ---

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


# --- Node Functions ---

async def retrieve(state: GraphState, retriever: PGVectorRetriever) -> GraphState:
    """Retrieve documents from vector store."""
    question = state["question"]
    logger.info(f"Retrieving documents for query: {question}")
    
    # Async retriever call
    documents = await retriever._aget_relevant_documents(question)
    
    logger.info(f"Retrieved {len(documents)} documents")
    return {"documents": documents, "question": question}


def grade_documents(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """Grade retrieved documents for relevance."""
    question = state["question"]
    documents = state["documents"]
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
    return {"filtered_documents": filtered_docs, "question": question}


def generate(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """Generate answer from filtered documents."""
    question = state["question"]
    documents = state.get("filtered_documents", state.get("documents", []))
    
    logger.info(f"Generating answer using {len(documents)} documents")
    
    # Check if we have documents
    if not documents:
        logger.warning("No relevant documents found for generation")
        return {
            "generation": "I don't have enough relevant information in the documents to answer this question.",
            "question": question,
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
    
    return {"generation": generation, "question": question}


# --- Graph Builder ---

def create_rag_graph(
    retriever: PGVectorRetriever,
    llm: ChatOpenAI,
) -> StateGraph:
    """
    Create the Agentic RAG graph.
    
    Flow:
    1. Retrieve documents from vector store
    2. Grade documents for relevance
    3. Generate answer from relevant documents
    """
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("retrieve", lambda state: retrieve(state, retriever))
    workflow.add_node("grade_documents", lambda state: grade_documents(state, llm))
    workflow.add_node("generate", lambda state: generate(state, llm))
    
    # Build graph
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_edge("grade_documents", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()


# --- Streaming Support ---

async def stream_rag_response(
    question: str,
    retriever: PGVectorRetriever,
    llm: ChatOpenAI,
):
    """
    Stream RAG response token by token.
    
    Yields:
        dict with 'type' and 'content' keys
    """
    logger.info(f"[Stream] Starting RAG stream for: {question[:50]}...")
    
    # Run retrieval and grading (non-streaming)
    state = {"question": question}
    
    # Execute retrieve step (async)
    state = await retrieve(state, retriever)
    yield {"type": "sources", "documents": state["documents"]}
    
    # Grade documents
    logger.info("[Stream] Grading documents...")
    state = grade_documents(state, llm)
    filtered_count = len(state.get("filtered_documents", []))
    logger.info(f"[Stream] {filtered_count} documents passed grading")
    
    if filtered_count == 0:
        logger.warning("[Stream] No relevant documents found")
        yield {"type": "token", "content": "I don't have enough relevant information to answer this question."}
        yield {"type": "done"}
        return
    
    # Stream generation
    documents = state["filtered_documents"]
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

