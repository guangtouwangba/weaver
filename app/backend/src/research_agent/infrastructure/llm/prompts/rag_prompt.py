"""RAG prompt templates."""

SYSTEM_PROMPT = """You are a research assistant helping users understand documents.
Answer questions based on the provided context from the documents.

Guidelines:
- If the answer is not in the context, say "I don't have enough information to answer this based on the provided documents."
- Always cite the source page numbers when possible using [Page X] format.
- Be concise but thorough.
- If asked to summarize, provide a structured summary with key points."""


def build_rag_prompt(query: str, context_chunks: list[dict]) -> str:
    """Build RAG prompt with context."""
    context = "\n\n".join(
        [f"[Page {c.get('page_number', '?')}]: {c['content']}" for c in context_chunks]
    )

    return f"""Context from documents:
{context}

User question: {query}

Please answer based on the context above."""

