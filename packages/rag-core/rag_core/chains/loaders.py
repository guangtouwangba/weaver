"""Document loading utilities."""

from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader

from rag_core.graphs.state import DocumentIngestState
from shared_config.settings import AppSettings


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


def _load_content_basic(temp_path: Path) -> str:
    """Load document content using standard loaders (no AI enhancement).
    
    This is the original implementation that uses format-specific loaders.
    """
    suffix = temp_path.suffix.lower()
    
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


def _load_content_with_langextract(temp_path: Path, settings: AppSettings) -> str:
    """Load document content enhanced with LangExtract AI processing.
    
    This implementation first uses standard loaders to extract text,
    then enhances it with LangExtract for better structure and understanding.
    """
    try:
        from rag_core.preprocessing.langextract_parser import create_langextract_parser
        
        # First, load with standard loaders
        base_content = _load_content_basic(temp_path)
        
        # Then enhance with LangExtract if enabled
        if settings.document_parser.enable_enhanced_parsing:
            print(f"  🤖 启用 LangExtract 智能增强...")
            
            # Get API key - try LangExtract specific first, then OpenRouter
            api_key = None
            if settings.document_parser.langextract_api_key:
                api_key = settings.document_parser.langextract_api_key.get_secret_value()
            elif settings.document_parser.openrouter_api_key:
                api_key = settings.document_parser.openrouter_api_key.get_secret_value()
            
            parser = create_langextract_parser(
                model_id=settings.document_parser.langextract_model_id,
                api_key=api_key,
                provider=settings.document_parser.langextract_provider,
                base_url=settings.document_parser.langextract_base_url,
                use_schema_constraints=settings.document_parser.langextract_use_schema,
                fence_output=settings.document_parser.langextract_fence_output,
            )
            
            enhanced_content = parser.parse_file(temp_path, base_content)
            print(f"  ✓ LangExtract 增强完成")
            return enhanced_content
        else:
            print(f"  ℹ️  LangExtract 增强已禁用，使用基础解析")
            return base_content
            
    except ImportError as e:
        print(f"  ⚠️  LangExtract 不可用: {e}")
        print(f"  └─ 回退到基础解析器")
        return _load_content_basic(temp_path)
    except Exception as e:
        print(f"  ⚠️  LangExtract 处理失败: {e}")
        print(f"  └─ 回退到基础解析器")
        return _load_content_basic(temp_path)


def load_document_content(temp_path: Path, settings: Optional[AppSettings] = None) -> str:
    """Read file and return text content based on file type and parser configuration.
    
    This function selects the appropriate parser based on configuration:
    - "default": Uses standard format-specific loaders (PyPDF, TextLoader, etc.)
    - "langextract": Uses AI-powered LangExtract for enhanced parsing
    
    Args:
        temp_path: Path to the document file
        settings: Application settings (loads from env if not provided)
        
    Returns:
        Extracted text content
    """
    suffix = temp_path.suffix.lower()
    
    print(f"📄 开始加载文档...")
    print(f"  ├─ 文件名: {temp_path.name}")
    print(f"  ├─ 文件类型: {suffix or '(无扩展名)'}")
    print(f"  └─ 文件大小: {temp_path.stat().st_size / 1024:.2f} KB")
    
    # Load settings if not provided
    if settings is None:
        settings = AppSettings()  # type: ignore[arg-type]
    
    parser_type = settings.document_parser.parser_type.lower()
    print(f"  ├─ 解析器类型: {parser_type}")
    
    # Select parser based on configuration
    if parser_type == "langextract":
        return _load_content_with_langextract(temp_path, settings)
    else:
        # Default to basic parsing
        return _load_content_basic(temp_path)
