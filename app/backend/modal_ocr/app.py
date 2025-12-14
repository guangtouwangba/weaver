"""Modal OCR Service - GPU-accelerated document parsing with Marker.

This module defines the Modal App for serverless OCR processing.
It supports both single-task and fan-out parallel processing for large documents.

Usage:
    # Deploy to Modal
    modal deploy app/backend/modal_ocr/app.py

    # Run locally for testing
    modal run app/backend/modal_ocr/app.py
"""

from typing import List, Literal, Optional

import modal

# Modal App definition
app = modal.App("research-agent-ocr")

# Configuration constants
PAGES_PER_CHUNK = 50  # Pages per parallel worker
SMALL_DOC_THRESHOLD = 50  # Documents <= this use single task
LARGE_DOC_PARALLEL_THRESHOLD = 150  # Documents > this use max parallelism

# Modal Volume for caching model weights (~5GB)
# Use a dedicated empty path that won't conflict with pip cache
VOLUME_PATH = "/data/marker-models"
marker_cache_volume = modal.Volume.from_name(
    "research-agent-marker-models",
    create_if_missing=True,
)
marker_cache = {VOLUME_PATH: marker_cache_volume}


# Lightweight image for coordinator (page counting only - NO GPU needed)
# This is very cheap: ~$0.0001/second on CPU
coordinator_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("pymupdf>=1.24.0")  # Only need PyMuPDF for page counting
)

# Heavy image for GPU OCR workers
# Use marker-pdf 1.x for latest stable API
inference_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1-mesa-glx", "libglib2.0-0", "poppler-utils")  # Required for OpenCV and PDF tools
    .pip_install(
        "marker-pdf>=1.0.0",  # Use new 1.x API
        "pymupdf>=1.24.0",  # For page count detection
    )
    .env({
        # Point all model caches to the persistent volume
        "HF_HOME": f"{VOLUME_PATH}/huggingface",
        "TORCH_HOME": f"{VOLUME_PATH}/torch",
        "TRANSFORMERS_CACHE": f"{VOLUME_PATH}/huggingface/transformers",
    })
)




def get_pdf_page_count(document: bytes) -> int:
    """Get the total page count of a PDF document.

    Args:
        document: PDF file content as bytes.

    Returns:
        Total number of pages in the PDF.
    """
    import fitz  # PyMuPDF

    with fitz.open(stream=document, filetype="pdf") as doc:
        return len(doc)


@app.function(
    gpu="l40s",
    timeout=600,
    retries=3,
    volumes=marker_cache,
    image=inference_image,
    scaledown_window=300,  # Keep container warm for 5 minutes
)
def parse_page_range(
    document: bytes,
    start_page: int,
    end_page: int,
    output_format: Literal["markdown", "html", "json"] = "markdown",
    force_ocr: bool = False,
) -> dict:
    """Parse a specific page range of a document using GPU-accelerated OCR.

    This function is designed to be called in parallel for large documents.

    Args:
        document: Document data (PDF) as bytes.
        start_page: First page to process (1-indexed).
        end_page: Last page to process (1-indexed, inclusive).
        output_format: Output format (markdown, html, or json).
        force_ocr: Force OCR even for text PDFs.

    Returns:
        Dict containing:
            - content: Parsed content in the specified format
            - start_page: Starting page number
            - end_page: Ending page number
            - has_ocr: Whether OCR was applied
            - error: Error message if parsing failed (None on success)
    """
    import os
    from tempfile import NamedTemporaryFile

    try:
        # Setup environment for model caching
        os.environ["HF_HOME"] = f"{VOLUME_PATH}/huggingface"
        os.environ["TORCH_HOME"] = f"{VOLUME_PATH}/torch"
        os.environ["TRANSFORMERS_CACHE"] = f"{VOLUME_PATH}/huggingface/transformers"
        os.environ["XDG_CACHE_HOME"] = VOLUME_PATH

        # Write document to temp file
        with NamedTemporaryFile(delete=False, mode="wb+", suffix=".pdf") as temp_file:
            temp_file.write(document)
            temp_path = temp_file.name

        print(f"Processing pages {start_page}-{end_page} from {temp_path}")

        # Use marker 1.x API
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
        from marker.config.parser import ConfigParser
        
        # Load models (cached in volume)
        print("Loading models...")
        artifact_dict = create_model_dict()
        print("Models loaded successfully")
        
        # Configure page range (0-indexed for marker 1.x)
        # Format: "start-end" where both are 0-indexed
        page_range_str = f"{start_page - 1}-{end_page - 1}"
        
        config = {
            "output_format": output_format,
            "page_range": page_range_str,
        }
        if force_ocr:
            config["force_ocr"] = True
        
        config_parser = ConfigParser(config)
        
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=artifact_dict,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
        )
        
        rendered = converter(temp_path)
        content, _, _ = text_from_rendered(rendered)

        # Log content extraction result
        content_len = len(content) if content else 0
        print(f"✅ Pages {start_page}-{end_page}: extracted {content_len} chars")
        if content_len == 0:
            print(f"⚠️ Warning: Empty content for pages {start_page}-{end_page}")

        # Check metadata for OCR info
        has_ocr = False
        if hasattr(rendered, 'metadata') and rendered.metadata:
            page_stats = getattr(rendered.metadata, 'page_stats', [])
            for stat in page_stats:
                if getattr(stat, 'text_extraction_method', '') == 'surya':
                    has_ocr = True
                    break

        return {
            "content": content,
            "start_page": start_page,
            "end_page": end_page,
            "has_ocr": has_ocr,
            "error": None,
        }

    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        print(f"Error processing pages {start_page}-{end_page}: {error_detail}")
        print(traceback.format_exc())
        return {
            "content": "",
            "start_page": start_page,
            "end_page": end_page,
            "has_ocr": False,
            "error": error_detail,
        }


@app.function(
    gpu="l40s",
    timeout=600,
    retries=3,
    volumes=marker_cache,
    image=inference_image,
    scaledown_window=300,  # Keep container warm for 5 minutes
)
def parse_document_single(
    document: bytes,
    output_format: Literal["markdown", "html", "json"] = "markdown",
    force_ocr: bool = False,
    page_range: Optional[str] = None,
) -> dict:
    """Parse an entire document as a single task (for small documents).

    Args:
        document: Document data (PDF, JPG, PNG) as bytes.
        output_format: Output format (markdown, html, or json).
        force_ocr: Force OCR even for text PDFs.
        page_range: Optional page range string (e.g., "1-10").

    Returns:
        Dict containing:
            - content: Full parsed content
            - page_count: Total pages processed
            - has_ocr: Whether OCR was applied
            - error: Error message if parsing failed (None on success)
    """
    import os
    from tempfile import NamedTemporaryFile

    try:
        # Setup environment for model caching
        os.environ["HF_HOME"] = f"{VOLUME_PATH}/huggingface"
        os.environ["TORCH_HOME"] = f"{VOLUME_PATH}/torch"
        os.environ["TRANSFORMERS_CACHE"] = f"{VOLUME_PATH}/huggingface/transformers"
        os.environ["XDG_CACHE_HOME"] = VOLUME_PATH

        # Write document to temp file
        with NamedTemporaryFile(delete=False, mode="wb+", suffix=".pdf") as temp_file:
            temp_file.write(document)
            temp_path = temp_file.name

        # Get page count
        page_count = get_pdf_page_count(document)
        print(f"Processing single document: {page_count} pages from {temp_path}")

        # Use marker 1.x API
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
        from marker.config.parser import ConfigParser
        
        # Load models (cached in volume)
        print("Loading models...")
        artifact_dict = create_model_dict()
        print("Models loaded successfully")
        
        # Build config
        config = {
            "output_format": output_format,
        }
        if force_ocr:
            config["force_ocr"] = True
        
        # Parse page range if provided (convert 1-indexed to 0-indexed)
        if page_range:
            parts = page_range.split("-")
            if len(parts) == 2:
                start_idx = int(parts[0]) - 1
                end_idx = int(parts[1]) - 1
                config["page_range"] = f"{start_idx}-{end_idx}"
        
        config_parser = ConfigParser(config)
        
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=artifact_dict,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
        )
        
        rendered = converter(temp_path)
        content, _, _ = text_from_rendered(rendered)

        # Log content extraction result
        content_len = len(content) if content else 0
        print(f"✅ Single task: extracted {content_len} chars from {page_count} pages")
        if content_len == 0:
            print(f"⚠️ Warning: Empty content from single task processing")

        # Check metadata for OCR info
        has_ocr = False
        if hasattr(rendered, 'metadata') and rendered.metadata:
            page_stats = getattr(rendered.metadata, 'page_stats', [])
            for stat in page_stats:
                if getattr(stat, 'text_extraction_method', '') == 'surya':
                    has_ocr = True
                    break

        return {
            "content": content,
            "page_count": page_count,
            "has_ocr": has_ocr,
            "error": None,
        }

    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        print(f"Error processing document: {error_detail}")
        print(traceback.format_exc())
        return {
            "content": "",
            "page_count": 0,
            "has_ocr": False,
            "error": error_detail,
        }


@app.function(
    timeout=900,
    image=coordinator_image,  # Lightweight image - only PyMuPDF, NO GPU needed!
)
def parse_document(
    document: bytes,
    output_format: Literal["markdown", "html", "json"] = "markdown",
    force_ocr: bool = False,
) -> dict:
    """Smart document parsing with automatic parallelization for large documents.

    This is the main entry point for document parsing. It automatically:
    - Uses single-task processing for small documents (<=50 pages)
    - Uses fan-out parallel processing for large documents (>50 pages)

    Args:
        document: Document data (PDF) as bytes.
        output_format: Output format (markdown, html, or json).
        force_ocr: Force OCR even for text PDFs.

    Returns:
        Dict containing:
            - content: Full parsed content (merged if parallel)
            - page_count: Total pages in document
            - has_ocr: Whether OCR was applied
            - processing_mode: "single" or "parallel"
            - chunks_processed: Number of parallel chunks (1 for single mode)
            - error: Error message if parsing failed (None on success)
    """
    try:
        # Get page count to determine processing strategy
        page_count = get_pdf_page_count(document)
        print(f"Document has {page_count} pages")

        # Small documents: single task processing
        if page_count <= SMALL_DOC_THRESHOLD:
            print(f"Using single-task processing for {page_count} pages")
            result = parse_document_single.remote(
                document=document,
                output_format=output_format,
                force_ocr=force_ocr,
            )
            result["processing_mode"] = "single"
            result["chunks_processed"] = 1
            return result

        # Large documents: fan-out parallel processing
        print(f"Using fan-out parallel processing for {page_count} pages")

        # Calculate page ranges
        page_ranges: List[tuple] = []
        for start in range(1, page_count + 1, PAGES_PER_CHUNK):
            end = min(start + PAGES_PER_CHUNK - 1, page_count)
            page_ranges.append((document, start, end, output_format, force_ocr))

        print(f"Splitting into {len(page_ranges)} parallel chunks")

        # Fan-out: parallel processing
        results = list(parse_page_range.starmap(page_ranges))

        # Check for errors
        errors = [r for r in results if r.get("error")]
        if errors:
            error_msgs = [f"Pages {r['start_page']}-{r['end_page']}: {r['error']}" for r in errors]
            return {
                "content": "",
                "page_count": page_count,
                "has_ocr": False,
                "processing_mode": "parallel",
                "chunks_processed": len(page_ranges),
                "error": f"Partial failures: {'; '.join(error_msgs)}",
            }

        # Merge results in page order
        results.sort(key=lambda r: r["start_page"])
        merged_content = "\n\n".join(r["content"] for r in results if r["content"])

        return {
            "content": merged_content,
            "page_count": page_count,
            "has_ocr": any(r.get("has_ocr", False) for r in results),
            "processing_mode": "parallel",
            "chunks_processed": len(page_ranges),
            "error": None,
        }

    except Exception as e:
        return {
            "content": "",
            "page_count": 0,
            "has_ocr": False,
            "processing_mode": "unknown",
            "chunks_processed": 0,
            "error": str(e),
        }


@app.local_entrypoint()
def main(document_filename: Optional[str] = None):
    """Local entrypoint for testing the Modal OCR service.

    Usage:
        modal run app/backend/modal_ocr/app.py --document-filename path/to/document.pdf
    """
    import urllib.request
    from pathlib import Path

    if document_filename is None:
        # Use a sample receipt image for testing
        document_url = "https://modal-cdn.com/cdnbot/Brandys-walmart-receipt-8g68_a_hk_f9c25fce.webp"
        print(f"No document provided, downloading sample from: {document_url}")
        request = urllib.request.Request(document_url)
        with urllib.request.urlopen(request) as response:
            document = response.read()
    else:
        document_path = Path(document_filename)
        if not document_path.exists():
            print(f"Error: File not found: {document_filename}")
            return

        print(f"Processing document: {document_filename}")
        document = document_path.read_bytes()

    # Parse the document
    result = parse_document.remote(document, output_format="markdown")

    if result.get("error"):
        print(f"Error: {result['error']}")
    else:
        print(f"\n{'='*60}")
        print(f"Processing mode: {result['processing_mode']}")
        print(f"Pages processed: {result['page_count']}")
        print(f"Chunks: {result['chunks_processed']}")
        print(f"OCR applied: {result['has_ocr']}")
        print(f"{'='*60}\n")
        print("Content preview (first 2000 chars):")
        print(result["content"][:2000])

