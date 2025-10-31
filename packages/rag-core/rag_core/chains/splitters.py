"""Text splitter utilities."""

from langchain.text_splitter import RecursiveCharacterTextSplitter

from rag_core.graphs.state import DocumentIngestState


def build_text_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    """Return a configured text splitter."""
    return RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


async def split_document(state: DocumentIngestState) -> DocumentIngestState:
    """Split document content into chunks and update state."""
    splitter = build_text_splitter(chunk_size=800, chunk_overlap=80)
    chunks = splitter.split_text(state.content)
    return state.copy(update={"chunks": chunks})
