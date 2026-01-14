import asyncio
import hashlib
import time
from typing import Any, Optional
from uuid import UUID

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from research_agent.domain.services.memory_service import MemoryService
from research_agent.infrastructure.llm.prompts.rag_prompt import build_mega_prompt
from research_agent.infrastructure.vector_store.langchain_pgvector import PGVectorRetriever
from research_agent.shared.utils.logger import logger
from research_agent.shared.utils.rag_trace import rag_log

# Cache for query rewriting
_rewrite_cache: dict[str, dict[str, str]] = {}


class GradeDocumentsModel(BaseModel):
    """Binary score for relevance check."""

    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")


def get_callbacks() -> list[Any]:
    """Get callbacks (dummy implementation to avoid circular import)."""
    return []


class RAGTools:
    """
    Encapsulates RAG capabilities as tools for the RAG Agent.
    Holds dependencies enabling tools to be stateless to the caller.
    """

    def __init__(
        self,
        project_id: UUID,
        session: Any,  # AsyncSession
        retriever: PGVectorRetriever | None = None,
        llm: ChatOpenAI | None = None,
        embedding_service: Any = None,
    ):
        self.project_id = project_id
        self.session = session
        self.retriever = retriever
        self.llm = llm
        self.embedding_service = embedding_service

    def get_tools(self) -> list[StructuredTool]:
        """Get the list of bound tools."""
        return [
            StructuredTool.from_function(
                func=self.vector_retrieve,
                name="vector_retrieve",
                description="Search for relevant documents in the vector database.",
            ),
            StructuredTool.from_function(
                func=self.rerank, name="rerank", description="Rerank documents based on relevance."
            ),
            StructuredTool.from_function(
                func=self.grade_documents,
                name="grade_documents",
                description="Filter documents for relevance.",
            ),
            StructuredTool.from_function(
                func=self.query_rewrite,
                name="query_rewrite",
                description="Rewrite query to be context-aware.",
            ),
            StructuredTool.from_function(
                func=self.retrieve_memory,
                name="retrieve_memory",
                description="Retrieve past memories.",
            ),
            StructuredTool.from_function(
                func=self.generate_answer,
                name="generate_answer",
                description="Generate final answer.",
            ),
        ]

    async def vector_retrieve(
        self,
        query: str,
        top_k: int = 5,
        doc_id_filter: str | None = None,
        use_hybrid_search: bool = False,
    ) -> list[Document]:
        """
        Search for relevant documents in the vector database using semantic similarity.

        Args:
            query: The search query string.
            top_k: Number of documents to retrieve (default: 5).
            doc_id_filter: Optional document ID to filter results (limit scope).
            use_hybrid_search: Whether to use hybrid search (keyword + vector).

        Returns:
            A list of found Documents.
        """
        if not self.retriever:
            logger.error("Retriever not initialized in RAGTools")
            return []

        start_time = time.time()

        # Configure retriever dynamically
        original_k = self.retriever.k
        original_hybrid = getattr(self.retriever, "use_hybrid_search", False)
        original_doc_id = getattr(self.retriever, "document_id", None)

        try:
            self.retriever.k = top_k
            self.retriever.use_hybrid_search = use_hybrid_search

            if doc_id_filter:
                self.retriever.document_id = doc_id_filter
                logger.info(f"[Retrieve] Applied filter: document_id={doc_id_filter}")

            # Execute retrieval
            logger.info(f"[Retrieve] searching: '{query}' (k={top_k}, hybrid={use_hybrid_search})")
            documents = await self.retriever._aget_relevant_documents(query)

        except Exception as e:
            logger.error(f"[Retrieve] Error: {e}")
            documents = []
        finally:
            # Restore state ensuring side-effects don't persist locally
            self.retriever.k = original_k
            self.retriever.use_hybrid_search = original_hybrid
            if doc_id_filter:
                self.retriever.document_id = original_doc_id

        # Metrics
        latency_ms = round((time.time() - start_time) * 1000, 2)
        top_similarity = max(
            [doc.metadata.get("similarity", 0.0) for doc in documents],
            default=0.0,
        )

        rag_log(
            "RETRIEVE",
            docs_count=len(documents),
            top_similarity=round(top_similarity, 3),
            search_type="hybrid" if use_hybrid_search else "vector",
            top_k=top_k,
            latency_ms=latency_ms,
        )

        logger.info(f"[Retrieve] Retrieved {len(documents)} documents in {latency_ms}ms")
        return documents

    async def rerank(
        self, query: str, documents: list[Document], active_doc_id: str | None = None
    ) -> list[Document]:
        """
        Rerank a list of documents based on relevance to the query using LLM scoring.

        Args:
            query: The search query.
            documents: List of documents to rerank.
            active_doc_id: Optional document ID that should always be ranked high.

        Returns:
            Reranked list of documents (top relevance first).
        """
        if not documents:
            return []

        if not self.llm:
            logger.warning("LLM not initialized in RAGTools, skipping rerank")
            return documents

        start_time = time.time()

        # Prompt for scoring
        system_prompt = """You are a document relevance scorer. Rate how relevant the given document
is to answering the user's question on a scale of 0-10.

0 = Completely irrelevant
5 = Somewhat relevant
10 = Highly relevant and directly answers the question

Output ONLY a single number between 0-10. No explanation."""

        score_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                (
                    "human",
                    "Question: {question}\\n\\nDocument: {document}\\n\\nRelevance score (0-10):",
                ),
            ]
        )

        chain = score_prompt | self.llm | StrOutputParser()

        max_concurrency = min(4, max(1, len(documents)))
        semaphore = asyncio.Semaphore(max_concurrency)

        async def score_one(doc: Document) -> tuple[float, Document]:
            doc_id = doc.metadata.get("document_id")
            if active_doc_id and doc_id == active_doc_id:
                return 10.0, doc

            doc_content = (
                doc.page_content[:2000] if len(doc.page_content) > 2000 else doc.page_content
            )

            async with semaphore:
                try:
                    result = await chain.ainvoke({"question": query, "document": doc_content})
                    try:
                        score = float(result.strip())
                    except ValueError:
                        score = 0.0
                    return score, doc
                except Exception as e:
                    logger.warning(f"Rerank failed for doc: {e}")
                    return 0.0, doc

        results = await asyncio.gather(*[score_one(doc) for doc in documents])

        results.sort(key=lambda x: x[0], reverse=True)
        # Keep documents with score > 0 (or all sorted)
        reranked_docs = [doc for score, doc in results if score > 3.0]
        # Fallback if filtered too many?
        if not reranked_docs and documents:
            reranked_docs = [doc for score, doc in results[:3]]

        latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"[Rerank] Reranked {len(documents)} -> {len(reranked_docs)} documents in {latency_ms}ms"
        )

        return reranked_docs

    async def grade_documents(self, query: str, documents: list[Document]) -> list[Document]:
        """
        Filter documents to only include those relevant to the query.

        Args:
            query: The search query.
            documents: List of documents to grade.

        Returns:
            List of relevant documents.
        """
        if not documents:
            return []

        if not self.llm:
            logger.warning("LLM not initialized in RAGTools, skipping grading")
            return documents

        start_time = time.time()

        structured_llm = self.llm.with_structured_output(GradeDocumentsModel)

        system_prompt = """You are a grader assessing relevance of a retrieved document to a user question. \n
    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
            ]
        )

        grader_chain = grade_prompt | structured_llm

        max_concurrency = min(4, max(1, len(documents)))
        semaphore = asyncio.Semaphore(max_concurrency)

        async def grade_one(doc: Document) -> Document | None:
            doc_content = (
                doc.page_content[:2000] if len(doc.page_content) > 2000 else doc.page_content
            )
            async with semaphore:
                try:
                    score = await grader_chain.ainvoke({"question": query, "document": doc_content})
                    if score.binary_score == "yes":
                        return doc
                    else:
                        return None
                except Exception as e:
                    logger.warning(f"[Grade] Grading failed: {e}")
                    return doc

        results = await asyncio.gather(*[grade_one(doc) for doc in documents])
        relevant_docs = [doc for doc in results if doc is not None]

        latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"[Grade] Filtered {len(documents)} -> {len(relevant_docs)} documents in {latency_ms}ms"
        )

        return relevant_docs

    async def query_rewrite(
        self, query: str, chat_history: list[Any], enable_cache: bool = True
    ) -> str:
        """
        Rewrite the query to be standalone and context-aware based on chat history.
        """
        if not chat_history:
            return query

        cache_key = None
        if enable_cache:
            try:
                # Assuming chat_history is list of tuples or similar
                # Just basic hashing for now
                key_str = f"{query}|{len(chat_history)}"
                cache_key = hashlib.md5(key_str.encode()).hexdigest()
                if cache_key in _rewrite_cache:
                    return _rewrite_cache[cache_key]["rewritten_question"]
            except Exception:
                pass

        if not self.llm:
            return query

        history_context = "\\n".join(
            [
                f"Human: {human}\\nAssistant: {ai}"
                for human, ai in chat_history[-3:]
                if isinstance(human, str) and isinstance(ai, str)
            ]
        )

        system_prompt = """You are a query rewriting assistant. Rewrite the user's question to be standalone.
Rules:
1. Resolve pronouns (it, that, them, etc.) with their actual referents
2. Include ONLY essential context from history
3. DO NOT add details the user didn't mention
4. Keep the question's original scope and openness
5. Output ONLY the rewritten question"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "History:\\n{history}\\n\\nQuestion: {question}\\n\\nRewrite:"),
            ]
        )

        chain = prompt | self.llm | StrOutputParser()

        try:
            rewritten = await chain.ainvoke({"history": history_context, "question": query})
            rewritten = rewritten.strip()

            if enable_cache and cache_key:
                _rewrite_cache[cache_key] = {"rewritten_question": rewritten}

            logger.info(f"[Rewrite] '{query}' -> '{rewritten}'")
            return rewritten
        except Exception as e:
            logger.error(f"Rewrite failed: {e}")
            return query

    async def retrieve_memory(
        self, query: str, limit: int = 5, min_similarity: float = 0.6
    ) -> list[dict]:
        """
        Retrieve relevant memories (past discussions) for the current query.
        """
        if not self.embedding_service or not self.session:
            logger.warning("[Memory] Dependencies not initialized")
            return []

        try:
            memory_service = MemoryService(
                session=self.session,
                embedding_service=self.embedding_service,
            )

            memories = await memory_service.retrieve_relevant_memories(
                project_id=self.project_id,
                query=query,
                limit=limit,
                min_similarity=min_similarity,
            )

            retrieved_memories = [
                {
                    "id": str(m.id),
                    "content": m.content,
                    "similarity": m.similarity,
                    "metadata": m.metadata,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in memories
            ]
            logger.info(f"[Memory] Retrieved {len(retrieved_memories)} relevant memories")
            return retrieved_memories
        except Exception as e:
            logger.error(f"[Memory] Failed to retrieve memories: {e}")
            return []

    async def generate_answer(
        self, query: str, documents: list[Document], intent_type: str = "factual"
    ) -> str:
        """
        Generate a final answer based on the query and provided documents.
        Uses Mega-Prompt with XML citations.
        """
        if not self.llm:
            return "LLM not initialized."

        # Convert documents to dict format for mega prompt
        doc_dicts = [
            {
                "document_id": doc.metadata.get("document_id", "unknown"),
                "filename": doc.metadata.get("filename", "Document"),
                "content": doc.page_content,
                "page_count": doc.metadata.get("page_count", 0),
            }
            for doc in documents
        ]

        mega_prompt = build_mega_prompt(query=query, documents=doc_dicts, intent_type=intent_type)

        try:
            response = await self.llm.ainvoke(mega_prompt)
            return response.content
        except Exception as e:
            logger.error(f"[Generate] Error: {e}")
            return "Failed to generate answer."
