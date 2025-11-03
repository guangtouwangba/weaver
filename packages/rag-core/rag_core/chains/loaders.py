"""Document loading utilities."""

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader

from rag_core.graphs.state import DocumentIngestState


async def load_document(state: DocumentIngestState) -> DocumentIngestState:
    """Return state unchanged when content already supplied."""
    if not state.content:
        raise ValueError("ingest payload missing content")
    return state


def _load_docx(file_path: Path) -> str:
    """Extract text from Word document using python-docx."""
    try:
        from docx import Document
    except ImportError as exc:
        raise ValueError("python-docx is required to load .docx files") from exc
    
    doc = Document(str(file_path))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n\n".join(paragraphs)


def load_document_content(temp_path: Path) -> str:
    """Read file and return text content based on file type."""
    suffix = temp_path.suffix.lower()
    
    print(f"📄 开始加载文档...")
    print(f"  ├─ 文件名: {temp_path.name}")
    print(f"  ├─ 文件类型: {suffix or '(无扩展名)'}")
    print(f"  └─ 文件大小: {temp_path.stat().st_size / 1024:.2f} KB")
    
    try:
        if suffix == ".pdf":
            # Load PDF files
            print(f"  📖 使用 PDF Loader 解析...")
            loader = PyPDFLoader(str(temp_path))
            documents = loader.load()
            content = "\n\n".join(doc.page_content for doc in documents)
            print(f"  ✓ PDF 解析完成，共 {len(documents)} 页")
            return content
        
        elif suffix == ".docx":
            # Load Word documents
            print(f"  📝 使用 Word Loader 解析...")
            content = _load_docx(temp_path)
            print(f"  ✓ Word 文档解析完成")
            return content
        
        elif suffix in [".txt", ".md", ".json", ".csv", ".log", ""]:
            # Load text files
            print(f"  📃 使用 Text Loader 解析...")
            try:
                loader = TextLoader(str(temp_path), encoding="utf-8")
                documents = loader.load()
                content = "\n\n".join(doc.page_content for doc in documents)
                print(f"  ✓ 文本文件解析完成 (UTF-8)")
                return content
            except UnicodeDecodeError:
                # Fallback to latin-1 for problematic text files
                print(f"  ⚠️ UTF-8 解码失败，尝试 Latin-1...")
                content = temp_path.read_text(encoding="latin-1")
                print(f"  ✓ 文本文件解析完成 (Latin-1)")
                return content
        
        else:
            # Unsupported file type
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported types: .pdf, .docx, .txt, .md, .json, .csv, .log"
            )
    
    except Exception as e:
        raise ValueError(f"Failed to load document {temp_path.name}: {str(e)}") from e
