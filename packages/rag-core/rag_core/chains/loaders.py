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
    
    try:
        if suffix == ".pdf":
            # Load PDF files
            loader = PyPDFLoader(str(temp_path))
            documents = loader.load()
            return "\n\n".join(doc.page_content for doc in documents)
        
        elif suffix == ".docx":
            # Load Word documents
            return _load_docx(temp_path)
        
        elif suffix in [".txt", ".md", ".json", ".csv", ".log", ""]:
            # Load text files
            try:
                loader = TextLoader(str(temp_path), encoding="utf-8")
                documents = loader.load()
                return "\n\n".join(doc.page_content for doc in documents)
            except UnicodeDecodeError:
                # Fallback to latin-1 for problematic text files
                return temp_path.read_text(encoding="latin-1")
        
        else:
            # Unsupported file type
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported types: .pdf, .docx, .txt, .md, .json, .csv, .log"
            )
    
    except Exception as e:
        raise ValueError(f"Failed to load document {temp_path.name}: {str(e)}") from e
