"""LangExtract-based document parser for intelligent text extraction.

This parser uses Google's langextract library to extract structured information
from documents with precise source grounding and better context understanding.

References:
- GitHub: https://github.com/google/langextract
- PyPI: https://pypi.org/project/langextract/
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import langextract as lx
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False


class LangExtractParser:
    """Parser using Google's langextract for intelligent document processing.
    
    This parser leverages LLMs to extract text with better understanding of
    document structure, tables, and semantic content.
    
    Args:
        model_id: LLM model to use for extraction (default: gemini-2.5-flash)
        api_key: API key for the LLM service (uses LANGEXTRACT_API_KEY env var if not provided)
        provider: LLM provider (gemini, openai, openrouter, ollama, etc.)
        base_url: Base URL for API (used for OpenRouter and custom endpoints)
        extraction_prompt: Custom prompt for text extraction
        use_schema_constraints: Whether to use schema constraints for extraction
        fence_output: Whether to fence the output
    
    Example:
        >>> # Using Gemini
        >>> parser = LangExtractParser(model_id="gemini-2.5-flash")
        
        >>> # Using OpenRouter
        >>> parser = LangExtractParser(
        ...     model_id="anthropic/claude-3-5-sonnet",
        ...     provider="openrouter",
        ...     api_key="sk-or-v1-..."
        ... )
    """
    
    def __init__(
        self,
        model_id: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        provider: str = "gemini",
        base_url: Optional[str] = None,
        extraction_prompt: Optional[str] = None,
        use_schema_constraints: bool = True,
        fence_output: bool = False,
    ):
        if not LANGEXTRACT_AVAILABLE:
            raise ImportError(
                "langextract is not installed. "
                "Install it with: pip install langextract"
            )
        
        self.model_id = model_id
        self.api_key = api_key or os.getenv("LANGEXTRACT_API_KEY")
        self.provider = provider
        self.base_url = base_url
        self.use_schema_constraints = use_schema_constraints
        self.fence_output = fence_output
        
        # OpenRouter specific: use OpenAI-compatible endpoint
        if provider == "openrouter":
            self.base_url = base_url or "https://openrouter.ai/api/v1"
            # OpenRouter requires fence_output and doesn't support schema constraints
            self.fence_output = True
            self.use_schema_constraints = False
            if not self.api_key:
                self.api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Default extraction prompt focuses on preserving document structure
        self.extraction_prompt = extraction_prompt or (
            "Extract all text content from this document. "
            "Preserve the document structure, paragraphs, and formatting. "
            "Include headings, sections, and maintain logical reading order. "
            "For tables, preserve their structure in a readable format. "
            "Return the complete text content."
        )
        
        print(f"🎯 初始化 LangExtract Parser...")
        print(f"  ├─ Model: {self.model_id}")
        print(f"  ├─ Provider: {self.provider}")
        if self.base_url:
            print(f"  ├─ Base URL: {self.base_url}")
        print(f"  └─ API Key: {'已配置' if self.api_key else '未配置'}")
    
    def parse_text(self, text: str) -> str:
        """Parse and extract structured text from raw text input.
        
        Args:
            text: Raw text to process
            
        Returns:
            Extracted and structured text
        """
        print(f"  📝 使用 LangExtract 处理文本...")
        print(f"     ├─ 输入长度: {len(text)} 字符")
        
        try:
            # Prepare langextract parameters
            extract_params = {
                "text_or_documents": text,
                "prompt_description": self.extraction_prompt,
                "examples": [],  # Can add few-shot examples if needed
                "model_id": self.model_id,
                "api_key": self.api_key,
                "use_schema_constraints": self.use_schema_constraints,
                "fence_output": self.fence_output,
            }
            
            # Add language_model_params for OpenRouter or custom endpoints
            if self.provider == "openrouter" or self.base_url:
                language_model_params = {}
                
                if self.base_url:
                    language_model_params["base_url"] = self.base_url
                
                # Add OpenRouter specific headers
                if self.provider == "openrouter":
                    site_url = os.getenv("OPENROUTER_SITE_URL")
                    site_name = os.getenv("OPENROUTER_SITE_NAME")
                    
                    extra_headers = {}
                    if site_url:
                        extra_headers["HTTP-Referer"] = site_url
                    if site_name:
                        extra_headers["X-Title"] = site_name
                    
                    if extra_headers:
                        language_model_params["extra_headers"] = extra_headers
                
                if language_model_params:
                    extract_params["language_model_params"] = language_model_params
            
            # Use langextract to intelligently process the text
            result = lx.extract(**extract_params)
            
            # Extract the processed text from result
            if hasattr(result, 'text'):
                extracted_text = result.text
            elif isinstance(result, str):
                extracted_text = result
            else:
                # Try to get text from result dictionary
                extracted_text = str(result)
            
            print(f"     ✓ LangExtract 处理完成")
            print(f"     └─ 输出长度: {len(extracted_text)} 字符")
            
            return extracted_text
            
        except Exception as e:
            print(f"     ⚠️  LangExtract 处理失败: {e}")
            print(f"     └─ 回退到原始文本")
            return text
    
    def parse_file(self, file_path: Path, loader_text: str) -> str:
        """Parse a document file using langextract after initial loading.
        
        LangExtract works best when applied to text that's already been extracted
        by format-specific loaders. This method takes pre-loaded text and enhances
        it with LangExtract's intelligent processing.
        
        Args:
            file_path: Path to the document file
            loader_text: Text already extracted by a format-specific loader
            
        Returns:
            Enhanced extracted text
        """
        print(f"  📄 LangExtract 增强处理...")
        print(f"     ├─ 文件: {file_path.name}")
        print(f"     ├─ 格式: {file_path.suffix}")
        
        # Use langextract to enhance the extracted text
        enhanced_text = self.parse_text(loader_text)
        
        return enhanced_text
    
    def supports_format(self, suffix: str) -> bool:
        """Check if this parser supports the given file format.
        
        LangExtract works as a post-processor for any text format.
        
        Args:
            suffix: File extension (e.g., '.pdf', '.docx')
            
        Returns:
            True (supports all formats as post-processor)
        """
        return True


def create_langextract_parser(
    model_id: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> LangExtractParser:
    """Factory function to create a LangExtract parser with configuration.
    
    Args:
        model_id: Model ID to use (default from env: LANGEXTRACT_MODEL_ID)
        api_key: API key (default from env: LANGEXTRACT_API_KEY or OPENROUTER_API_KEY)
        provider: LLM provider (default from env: LANGEXTRACT_PROVIDER)
        base_url: Base URL for API (default from env: LANGEXTRACT_BASE_URL)
        **kwargs: Additional arguments for LangExtractParser
        
    Returns:
        Configured LangExtractParser instance
        
    Example:
        >>> # Using OpenRouter
        >>> parser = create_langextract_parser(
        ...     provider="openrouter",
        ...     model_id="anthropic/claude-3-5-sonnet"
        ... )
    """
    model_id = model_id or os.getenv("LANGEXTRACT_MODEL_ID", "gemini-2.5-flash")
    provider = provider or os.getenv("LANGEXTRACT_PROVIDER", "gemini")
    base_url = base_url or os.getenv("LANGEXTRACT_BASE_URL")
    
    # Smart API key resolution based on provider
    if not api_key:
        if provider == "openrouter":
            # For OpenRouter: try OPENROUTER_API_KEY first, then LANGEXTRACT_API_KEY
            api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LANGEXTRACT_API_KEY")
            
            # Also try loading from settings if available
            if not api_key:
                try:
                    from shared_config.settings import AppSettings
                    settings = AppSettings()  # type: ignore[arg-type]
                    if settings.document_parser.openrouter_api_key:
                        api_key = settings.document_parser.openrouter_api_key.get_secret_value()
                    elif settings.document_parser.langextract_api_key:
                        api_key = settings.document_parser.langextract_api_key.get_secret_value()
                except Exception:
                    pass  # Fallback to env vars already tried above
        else:
            # For other providers: try LANGEXTRACT_API_KEY
            api_key = os.getenv("LANGEXTRACT_API_KEY")
            
            # Also try loading from settings if available
            if not api_key:
                try:
                    from shared_config.settings import AppSettings
                    settings = AppSettings()  # type: ignore[arg-type]
                    if settings.document_parser.langextract_api_key:
                        api_key = settings.document_parser.langextract_api_key.get_secret_value()
                except Exception:
                    pass
    
    return LangExtractParser(
        model_id=model_id,
        api_key=api_key,
        provider=provider,
        base_url=base_url,
        **kwargs
    )


# Example usage
if __name__ == "__main__":
    # Example: Parse a document
    parser = create_langextract_parser()
    
    sample_text = """
    This is a sample document with multiple sections.
    
    Section 1: Introduction
    This section introduces the topic.
    
    Section 2: Methods
    This section describes the methods used.
    """
    
    result = parser.parse_text(sample_text)
    print("\n" + "="*80)
    print("Extracted Text:")
    print("="*80)
    print(result)

