"""Answer synthesis chain helpers."""

from typing import List

from langchain.chains.llm import LLMChain
from langchain_community.llms import FakeListLLM
from langchain.prompts import PromptTemplate

from rag_core.graphs.state import QueryState


def build_answer_chain() -> LLMChain:
    """Return an LLMChain that summarizes retrieved chunks."""
    prompt = PromptTemplate.from_template(
        "You are a helpful assistant. Given the following context: {context}\n"
        "Answer the question: {question}"
    )
    llm = FakeListLLM(responses=["This is a placeholder answer."])
    return LLMChain(prompt=prompt, llm=llm)


def synthesize_answer(state: QueryState) -> QueryState:
    """Produce an answer using the answer chain."""
    chain = build_answer_chain()
    documents: List[dict] = state.documents or []
    context = "\n".join(doc.get("page_content", "") for doc in documents)
    result = chain.invoke({"context": context, "question": state.question})
    return state.model_copy(update={"answer": result["text"]})
