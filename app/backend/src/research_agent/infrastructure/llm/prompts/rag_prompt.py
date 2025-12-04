"""RAG prompt templates."""

SYSTEM_PROMPT = """You are a research assistant helping users understand documents.
Answer questions based on the provided context from the documents.

Guidelines:
- **Provide comprehensive and detailed answers.** Do not be too brief.
- **Expand on key details.** When the context contains explanations, examples, or reasoning, include them in your answer.
- If the answer is not in the context, say "I don't have enough information to answer this based on the provided documents."
- Always cite the source page numbers when possible using [Page X] format.
- Structure your answer clearly. Use paragraphs for explanations and bullet points for lists.
- Answer in the same language as the user's question.
"""


# Intent Classification Prompt
INTENT_CLASSIFICATION_PROMPT = """You are a question intent classifier. Classify the user's question into ONE of these types:

1. **factual**: Questions seeking specific facts or definitions
   - Examples: "什么是X?", "X的定义是什么?", "What is X?", "Define X"

2. **conceptual**: Questions seeking understanding of concepts or principles
   - Examples: "如何理解X?", "X的原理是什么?", "How does X work?", "Explain the concept of X"

3. **comparison**: Questions comparing two or more items
   - Examples: "X和Y的区别?", "X vs Y", "Compare X and Y", "What's the difference between X and Y?"

4. **howto**: Questions seeking procedural or step-by-step instructions
   - Examples: "如何做X?", "X的步骤", "How to do X?", "Steps to accomplish X"

5. **summary**: Questions seeking a summary or overview
   - Examples: "总结X", "X的要点", "Summarize X", "Give me an overview of X"

6. **explanation**: Questions seeking causal explanations or reasoning
   - Examples: "为什么X?", "X的原因", "Why does X happen?", "What causes X?"

Output ONLY a JSON object with this format:
{{
  "intent": "factual|conceptual|comparison|howto|summary|explanation",
  "confidence": 0.95
}}

Be concise. Output only the JSON, nothing else."""


# Generation prompts for different intents
GENERATION_PROMPTS = {
    "factual": """You are a research assistant. Provide a concise, factual answer (1-2 sentences). Be direct and precise.
Answer in the same language as the question.""",
    "conceptual": """You are a research assistant. Provide a detailed explanation with principles and examples.
Help the user understand the concept deeply. Answer in the same language as the question.""",
    "comparison": """You are a research assistant. Compare the items using a clear structure (table or bullet points).
Highlight key similarities and differences. Answer in the same language as the question.""",
    "howto": """You are a research assistant. Provide step-by-step instructions in a numbered list format.
Be clear and actionable. Answer in the same language as the question.""",
    "summary": """You are a research assistant. Provide a comprehensive summary with key points in bullet format.
Cover all important aspects. Answer in the same language as the question.""",
    "explanation": """You are a research assistant. Explain the reasoning and causality.
Help the user understand why and how things work. Answer in the same language as the question.""",
}


def build_rag_prompt(query: str, context_chunks: list[dict]) -> str:
    """Build RAG prompt with context."""
    context = "\n\n".join(
        [f"[Page {c.get('page_number', '?')}]: {c['content']}" for c in context_chunks]
    )

    return f"""Context from documents:
{context}

User question: {query}

Please answer the question above **in detail** based on the context.
Ensure you incorporate all relevant information from the documents to provide a thorough explanation."""


def get_generation_prompt(intent_type: str) -> str:
    """Get generation prompt for specific intent type."""
    return GENERATION_PROMPTS.get(intent_type, GENERATION_PROMPTS["factual"])


# Long Context Mode Prompt
LONG_CONTEXT_SYSTEM_PROMPT = """You are a research assistant helping users understand documents.
You have access to the FULL CONTENT of the documents, not just snippets.

**CRITICAL: You MUST cite your sources for every factual claim.**

Citation Format:
- Inline format: [document_id:page_number:char_start:char_end]
  Example: "RAG stands for Retrieval-Augmented Generation [abc123:1:0:50]."

- Structured format (for complex citations):
  {{
    "text": "Your statement here",
    "citations": [
      {{
        "document_id": "abc123",
        "page_number": 1,
        "char_start": 0,
        "char_end": 50,
        "snippet": "RAG stands for Retrieval-Augmented Generation"
      }}
    ]
  }}

Guidelines:
1. **Cite every factual claim** - Every statement that comes from the documents must have a citation
2. **Use precise character positions** - The char_start and char_end should point to the exact text in the document
3. **Multiple citations allowed** - If information comes from multiple sources, cite all of them
4. **Answer comprehensively** - Use the full context to provide detailed, well-reasoned answers
5. **Maintain accuracy** - Only state facts that are explicitly in the provided documents
6. **Answer in the same language as the user's question**

Document boundaries are marked with:
--- Document: [filename] (ID: [document_id]) ---

Use these markers to identify which document you're citing."""


def build_long_context_prompt(
    query: str,
    documents: list[dict],
    citation_format: str = "both",
) -> str:
    """
    Build long context prompt with full document content.

    Args:
        query: User question
        documents: List of document dicts with keys:
            - document_id: UUID
            - filename: str
            - content: str (full content)
            - page_count: int (optional)
            - metadata: dict (optional)
        citation_format: "inline" | "structured" | "both"

    Returns:
        Formatted prompt string
    """
    # Build document sections
    doc_sections = []
    for i, doc in enumerate(documents, 1):
        doc_id = doc.get("document_id", "unknown")
        filename = doc.get("filename", f"Document {i}")
        content = doc.get("content", "")
        page_count = doc.get("page_count", 0)

        section = f"--- Document {i}: {filename} (ID: {doc_id})"
        if page_count > 0:
            section += f", {page_count} pages"
        section += " ---\n\n"
        section += content
        doc_sections.append(section)

    documents_text = "\n\n".join(doc_sections)

    # Build citation format instructions
    citation_instructions = ""
    if citation_format in ("inline", "both"):
        citation_instructions += """
Inline Citation Format:
After each factual statement, add: [document_id:page_number:char_start:char_end]
Example: "RAG improves accuracy [abc123:1:0:50]."
"""

    if citation_format in ("structured", "both"):
        citation_instructions += """
Structured Citation Format:
For complex citations, use JSON:
{{
  "text": "Your statement",
  "citations": [
    {{
      "document_id": "abc123",
      "page_number": 1,
      "char_start": 0,
      "char_end": 50,
      "snippet": "Quoted text"
    }}
  ]
}}
"""

    prompt = f"""Full Document Content:

{documents_text}

---

User Question: {query}

{citation_instructions}

Please answer the question above based on the FULL DOCUMENT CONTENT provided.
Remember to cite every factual claim using the citation format specified above.
Be comprehensive and use all relevant information from the documents."""

    return prompt
