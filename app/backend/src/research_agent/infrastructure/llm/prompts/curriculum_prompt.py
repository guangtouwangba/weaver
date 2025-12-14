"""Curriculum generation prompt templates."""

from typing import List, Dict, Any

SYSTEM_PROMPT = """You are an expert curriculum designer and educational content strategist.
Your task is to create a personalized learning path based on the documents provided by the user.

Guidelines:
- Analyze the documents to understand the overall knowledge structure and progression.
- Design a logical learning sequence that builds knowledge step by step.
- Each step should focus on a specific concept or topic.
- Estimate realistic time durations for each learning step (in minutes).
- Cite the specific document and page range for each step.
- Organize steps from foundational concepts to advanced topics.
- Aim for 4-8 learning steps for a comprehensive curriculum.
- Keep step titles clear, concise, and descriptive."""


def build_curriculum_prompt(documents: List[Dict[str, Any]]) -> str:
    """Build curriculum generation prompt with document context.
    
    Args:
        documents: List of document metadata with intro content.
                  Each dict should have: id, title, intro_content, page_count
    
    Returns:
        Formatted prompt string for LLM.
    """
    if not documents:
        return "No documents available to create a curriculum."
    
    # Build document context
    doc_context = []
    for i, doc in enumerate(documents, 1):
        title = doc.get("title", f"Document {i}")
        intro = doc.get("intro_content", "")
        pages = doc.get("page_count", "?")
        
        doc_context.append(
            f"Document {i}: {title}\n"
            f"Pages: {pages}\n"
            f"Introduction:\n{intro}\n"
        )
    
    context_text = "\n---\n".join(doc_context)
    
    return f"""I have uploaded the following documents for learning:

{context_text}

Based on these documents, please generate a comprehensive learning curriculum.

For each learning step, provide:
1. A clear, descriptive title
2. The source document filename (use the exact title provided above)
3. The source type (always "document" for PDFs)
4. The recommended page range to study (e.g., "p.1-5" or "p.10-15")
5. Estimated study duration in minutes

Return the curriculum as a JSON array with this exact structure:
[
  {{
    "title": "Introduction to Core Concepts",
    "source": "Document 1: [exact title]",
    "sourceType": "document",
    "pageRange": "p.1-10",
    "duration": 15
  }},
  ...
]

Ensure the steps follow a logical progression from basics to advanced topics."""

