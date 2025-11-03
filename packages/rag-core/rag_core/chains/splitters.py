"""Text splitter utilities."""

from langchain.text_splitter import RecursiveCharacterTextSplitter

from rag_core.graphs.state import DocumentIngestState


def build_text_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    """Return a configured text splitter."""
    return RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


async def split_document(state: DocumentIngestState) -> DocumentIngestState:
    """Split document content into chunks and update state."""
    print(f"✂️ 开始分割文档...")
    print(f"  ├─ 文档长度: {len(state.content)} 字符")
    print(f"  ├─ Chunk 大小: 800")
    print(f"  └─ 重叠大小: 80")
    
    splitter = build_text_splitter(chunk_size=800, chunk_overlap=80)
    chunks = splitter.split_text(state.content)
    
    print(f"✅ 文档分割完成!")
    print(f"  ├─ 生成 Chunks: {len(chunks)}")
    print(f"  └─ 平均长度: {sum(len(c) for c in chunks) // len(chunks) if chunks else 0} 字符")
    
    return state.model_copy(update={"chunks": chunks})
