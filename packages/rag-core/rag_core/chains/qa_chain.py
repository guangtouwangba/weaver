"""Answer synthesis chain helpers."""

from typing import List

from langchain.chains.llm import LLMChain
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

from rag_core.chains.llm import build_llm
from rag_core.graphs.state import QueryState
from shared_config.settings import AppSettings


def build_answer_chain() -> LLMChain:
    """Return an LLMChain that summarizes retrieved chunks.

    Uses the configured LLM provider (fake/openai/openrouter) from settings.
    The prompt is designed to match the language of the user's question.
    """
    settings = AppSettings()  # type: ignore[arg-type]
    llm = build_llm(settings)

    # System message for consistent behavior
    system_template = (
        "You are a helpful RAG (Retrieval-Augmented Generation) assistant. "
        "Your job is to answer questions based ONLY on the provided context. "
        "CRITICAL RULE: Always respond in the SAME LANGUAGE as the user's question. "
        "If the question is in Chinese (中文), answer in Chinese. "
        "If the question is in English, answer in English. "
        "Never mix languages unless the question does."
    )
    
    # Human message template with context and question
    human_template = (
        "Context (reference material):\n"
        "---\n"
        "{context}\n"
        "---\n\n"
        "User Question: {question}\n\n"
        "Please provide a clear and accurate answer based on the context above. "
        "Remember: Use the SAME LANGUAGE as my question."
    )
    
    # Try to use ChatPromptTemplate for better language control
    try:
        system_message = SystemMessagePromptTemplate.from_template(system_template)
        human_message = HumanMessagePromptTemplate.from_template(human_template)
        chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        return LLMChain(prompt=chat_prompt, llm=llm)
    except Exception:
        # Fallback to simple PromptTemplate if ChatPromptTemplate not supported
        from langchain.prompts import PromptTemplate
        simple_prompt = PromptTemplate.from_template(
            system_template + "\n\n" + human_template
        )
        return LLMChain(prompt=simple_prompt, llm=llm)


def synthesize_answer(state: QueryState) -> QueryState:
    """Produce an answer using the answer chain."""
    chain = build_answer_chain()
    documents: List[dict] = state.documents or []
    context = "\n".join(doc.get("page_content", "") for doc in documents)
    result = chain.invoke({"context": context, "question": state.question})
    return state.model_copy(update={"answer": result["text"]})
