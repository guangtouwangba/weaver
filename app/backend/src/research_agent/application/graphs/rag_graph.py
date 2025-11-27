"""Agentic RAG workflow using LangGraph (Corrective RAG pattern)."""

from typing import List, TypedDict, Annotated

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from research_agent.infrastructure.vector_store.langchain_pgvector import PGVectorRetriever


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

def retrieve(state: GraphState, retriever: PGVectorRetriever) -> GraphState:
    """Retrieve documents from vector store."""
    question = state["question"]
    
    # Synchronous call wrapper for async retriever
    import asyncio
    loop = asyncio.get_event_loop()
    documents = loop.run_until_complete(retriever._aget_relevant_documents(question))
    
    return {"documents": documents, "question": question}


def grade_documents(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """Grade retrieved documents for relevance."""
    question = state["question"]
    documents = state["documents"]
    
    # LLM with structured output for grading
    llm_with_tool = llm.with_structured_output(GradeDocuments)
    
    # Prompt
    system_prompt = """You are a grader assessing relevance of a retrieved document to a user question.
    If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant.
    Give a binary score 'yes' or 'no' to indicate whether the document is relevant to the question."""
    
    grade_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ])
    
    chain = grade_prompt | llm_with_tool
    
    # Grade each document
    filtered_docs = []
    for doc in documents:
        score = chain.invoke({"question": question, "document": doc.page_content})
        if score.binary_score == "yes":
            filtered_docs.append(doc)
    
    return {"filtered_documents": filtered_docs, "question": question}


def generate(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """Generate answer from filtered documents."""
    question = state["question"]
    documents = state.get("filtered_documents", state.get("documents", []))
    
    # Check if we have documents
    if not documents:
        return {
            "generation": "I don't have enough relevant information in the documents to answer this question.",
            "question": question,
        }
    
    # Build context from documents
    context = "\n\n".join([doc.page_content for doc in documents])
    
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
    
    generation = chain.invoke({"question": question, "context": context})
    
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
    # Create graph
    graph = create_rag_graph(retriever, llm)
    
    # Run retrieval and grading (non-streaming)
    state = {"question": question}
    
    # Execute retrieve and grade steps
    state = retrieve(state, retriever)
    yield {"type": "sources", "documents": state["documents"]}
    
    state = grade_documents(state, llm)
    filtered_count = len(state.get("filtered_documents", []))
    
    if filtered_count == 0:
        yield {"type": "token", "content": "I don't have enough relevant information to answer this question."}
        yield {"type": "done"}
        return
    
    # Stream generation
    documents = state["filtered_documents"]
    context = "\n\n".join([doc.page_content for doc in documents])
    
    system_prompt = """You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Question: {question}\n\nContext: {context}\n\nAnswer:"),
    ])
    
    # Create streaming LLM
    streaming_llm = llm.with_config({"streaming": True})
    chain = prompt | streaming_llm | StrOutputParser()
    
    # Stream tokens
    async for token in chain.astream({"question": question, "context": context}):
        yield {"type": "token", "content": token}
    
    yield {"type": "done"}

