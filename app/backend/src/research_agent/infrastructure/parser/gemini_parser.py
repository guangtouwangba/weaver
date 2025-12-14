"""Gemini-based document parser implementation.

This parser uses Google's Gemini 2.0 Flash model for Vision OCR to extract
text from PDF documents. It converts PDF pages to images and uses Gemini's
multimodal capabilities for intelligent text extraction with structure preservation.

Supports parallel processing of pages for faster OCR of large documents.
"""

import asyncio
import io
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from research_agent.config import get_settings
from research_agent.infrastructure.parser.base import (
    DocumentParser,
    DocumentParsingError,
    DocumentType,
    ParsedPage,
    ParseResult,
)
from research_agent.shared.utils.logger import logger

# Google API endpoint for connectivity check
GOOGLE_API_HOST = "generativelanguage.googleapis.com"
GOOGLE_API_PORT = 443


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


@dataclass
class PageResult:
    """Result of processing a single page."""

    page_number: int
    content: str
    char_count: int
    api_duration: float
    success: bool
    error: Optional[str] = None


# Default OCR prompt following the blog's best practices
DEFAULT_OCR_PROMPT = """Extract ALL text content from this document page.

Requirements:
1. Preserve the document structure including headers, paragraphs, and sections.
2. For tables: maintain the table structure using markdown table format.
3. For multi-column layouts: process columns from left to right, clearly separating content.
4. For lists: preserve bullet points and numbering.
5. Include all headers, footers, page numbers, and footnotes.
6. Output the extracted text in clean Markdown format.

If any text is unclear or uncertain, mark it with [?].
"""


class GeminiParser(DocumentParser):
    """
    Gemini Vision-based document parser for PDF OCR.

    This parser converts PDF pages to high-resolution images and uses
    Google's Gemini 2.0 Flash model to extract text with structure preservation.

    Features:
    - High-quality OCR using Vision LLM
    - Structure-aware text extraction
    - Markdown output format
    - Handles complex layouts (tables, multi-column, etc.)
    - Parallel processing for large documents
    """

    SUPPORTED_MIME_TYPES = ["application/pdf"]
    SUPPORTED_EXTENSIONS = [".pdf"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash",
        dpi: int = 300,
        ocr_prompt: Optional[str] = None,
        concurrency: Optional[int] = None,
        request_timeout: Optional[int] = None,
        connection_timeout: Optional[int] = None,
    ):
        """
        Initialize the Gemini parser.

        Args:
            api_key: Google API key. If not provided, uses settings.
            model: Gemini model to use (default: gemini-2.0-flash).
            dpi: DPI for PDF to image conversion (default: 300).
            ocr_prompt: Custom OCR prompt. If not provided, uses default.
            concurrency: Number of parallel API calls. If not provided, uses settings.
            request_timeout: Timeout for each API request in seconds.
            connection_timeout: Timeout for connectivity check in seconds.
        """
        settings = get_settings()
        self.api_key = api_key or settings.google_api_key
        self.model_name = model
        self.dpi = dpi
        self.ocr_prompt = ocr_prompt or DEFAULT_OCR_PROMPT
        self.concurrency = concurrency or settings.gemini_ocr_concurrency
        self.request_timeout = request_timeout or settings.gemini_request_timeout
        self.connection_timeout = connection_timeout or settings.gemini_connection_timeout
        self._client = None
        self._connectivity_checked = False

    def _check_connectivity(self) -> bool:
        """
        Check if Google's Gemini API is reachable.

        Returns:
            True if connectivity is OK, raises DocumentParsingError otherwise.
        """
        if self._connectivity_checked:
            return True

        logger.info(f"[GeminiOCR] Checking connectivity to {GOOGLE_API_HOST}:{GOOGLE_API_PORT}...")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connection_timeout)
            result = sock.connect_ex((GOOGLE_API_HOST, GOOGLE_API_PORT))
            sock.close()

            if result == 0:
                logger.info("[GeminiOCR] ✓ Connectivity check passed")
                self._connectivity_checked = True
                return True
            else:
                raise DocumentParsingError(
                    f"Cannot connect to Google Gemini API ({GOOGLE_API_HOST}:{GOOGLE_API_PORT}). "
                    f"Connection returned error code: {result}\n\n"
                    "Possible causes:\n"
                    "  1. Network firewall blocking Google services\n"
                    "  2. VPN blocking outbound connections to Google\n"
                    "  3. Running in a region where Google is blocked (e.g., China mainland)\n"
                    "  4. No internet connectivity\n\n"
                    "Solutions:\n"
                    "  - Try disabling VPN or using a different network\n"
                    "  - Set OCR_MODE=unstructured to use offline OCR instead\n"
                    "  - Contact your network administrator"
                )
        except socket.timeout:
            raise DocumentParsingError(
                f"Connection to Google Gemini API timed out after {self.connection_timeout}s. "
                f"Cannot reach {GOOGLE_API_HOST}:{GOOGLE_API_PORT}.\n\n"
                "This usually indicates:\n"
                "  1. Network firewall/proxy blocking connections to Google\n"
                "  2. Running in China or other regions where Google is blocked\n"
                "  3. VPN interfering with connections\n\n"
                "Solutions:\n"
                "  - Set OCR_MODE=unstructured to use offline OCR\n"
                "  - Try a different network or disable VPN\n"
                "  - Use a proxy that allows Google API access"
            )
        except socket.gaierror as e:
            raise DocumentParsingError(
                f"DNS resolution failed for {GOOGLE_API_HOST}: {e}\n\n"
                "This indicates a DNS issue. Solutions:\n"
                "  - Check your DNS settings\n"
                "  - Try using Google DNS (8.8.8.8) or Cloudflare DNS (1.1.1.1)\n"
                "  - Set OCR_MODE=unstructured to use offline OCR"
            )
        except Exception as e:
            raise DocumentParsingError(
                f"Connectivity check failed: {e}\n\n"
                "Set OCR_MODE=unstructured to use offline OCR as fallback."
            )

    def _get_client(self):
        """Lazy initialization of Gemini client with connectivity check."""
        if self._client is None:
            if not self.api_key:
                raise DocumentParsingError(
                    "Google API key not configured. Set GOOGLE_API_KEY environment variable."
                )

            # Check connectivity first
            self._check_connectivity()

            try:
                import google.generativeai as genai

                # Configure with timeout settings
                genai.configure(
                    api_key=self.api_key,
                    transport="rest",  # Use REST instead of gRPC for better timeout control
                )
                self._client = genai.GenerativeModel(
                    self.model_name,
                    generation_config={
                        "candidate_count": 1,
                    },
                )
                logger.info(
                    f"Gemini client initialized with model: {self.model_name} "
                    f"(timeout: {self.request_timeout}s)"
                )
            except ImportError as e:
                raise DocumentParsingError(
                    "google-generativeai library not installed. "
                    "Install with: pip install google-generativeai",
                    cause=e,
                )
        return self._client

    def supported_formats(self) -> List[str]:
        """Return list of supported MIME types."""
        return self.SUPPORTED_MIME_TYPES.copy()

    def supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()

    async def parse(self, file_path: str) -> ParseResult:
        """
        Parse a PDF file using Gemini Vision OCR with parallel processing.

        Args:
            file_path: Path to the PDF file.

        Returns:
            ParseResult containing pages and metadata.

        Raises:
            DocumentParsingError: If parsing fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentParsingError(f"File not found: {file_path}", file_path=file_path)

        logger.info(f"Parsing PDF with Gemini Vision OCR: {file_path}")

        try:
            result = await self._parse_parallel(file_path)
            return result
        except DocumentParsingError:
            raise
        except Exception as e:
            logger.error(f"Gemini parsing failed for {file_path}: {e}", exc_info=True)
            raise DocumentParsingError(
                f"Failed to parse document with Gemini: {e}",
                file_path=file_path,
                cause=e,
            )

    async def _parse_parallel(self, file_path: str) -> ParseResult:
        """Parallel parsing implementation using asyncio."""
        from pdf2image import convert_from_path

        total_start_time = time.time()
        filename = Path(file_path).name
        settings = get_settings()

        logger.info(f"{'=' * 60}")
        logger.info(f"[GeminiOCR] Starting PARALLEL OCR for: {filename}")
        logger.info(
            f"[GeminiOCR] Model: {self.model_name} | DPI: {self.dpi} | Workers: {self.concurrency}"
        )
        logger.info(f"{'=' * 60}")

        # Step 1: Initialize Gemini client
        logger.info("[GeminiOCR] Step 1/3: Initializing Gemini client...")
        client_start = time.time()
        client = self._get_client()
        client_duration = time.time() - client_start
        logger.info(f"[GeminiOCR] ✓ Client ready ({_format_duration(client_duration)})")

        # Step 2: Convert PDF to images (this must be synchronous)
        logger.info(f"[GeminiOCR] Step 2/3: Converting PDF to images at {self.dpi} DPI...")
        convert_start = time.time()
        try:
            images = await asyncio.to_thread(convert_from_path, file_path, dpi=self.dpi)
        except Exception as e:
            raise DocumentParsingError(
                f"Failed to convert PDF to images: {e}. "
                "Make sure poppler-utils is installed (brew install poppler on macOS).",
                file_path=file_path,
                cause=e,
            )
        convert_duration = time.time() - convert_start

        page_count = len(images)
        logger.info(
            f"[GeminiOCR] ✓ Converted {page_count} pages to images "
            f"({_format_duration(convert_duration)})"
        )

        # Log image details
        if images:
            first_img = images[0]
            logger.info(f"[GeminiOCR]   Image size: {first_img.width}x{first_img.height} pixels")

        # Step 3: Process pages in parallel
        logger.info(
            f"[GeminiOCR] Step 3/3: Processing {page_count} pages with {self.concurrency} parallel workers..."
        )
        logger.info(f"[GeminiOCR] {'─' * 50}")

        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.concurrency)

        # Track progress
        completed_count = 0
        completed_lock = asyncio.Lock()

        async def process_page_with_progress(page_idx: int, image) -> PageResult:
            """Process a single page with semaphore and progress tracking."""
            nonlocal completed_count
            page_number = page_idx + 1

            async with semaphore:
                logger.info(f"[GeminiOCR] 📄 Page {page_number}/{page_count} - Starting...")

                page_start = time.time()
                try:
                    # Run the synchronous API call in a thread
                    content, api_duration = await asyncio.to_thread(
                        self._extract_text_from_image_sync, client, image, page_number, page_count
                    )
                    page_duration = time.time() - page_start

                    async with completed_lock:
                        completed_count += 1
                        progress_pct = (completed_count / page_count) * 100

                    logger.info(
                        f"[GeminiOCR] ✓ Page {page_number} complete: "
                        f"{len(content):,} chars "
                        f"(API: {_format_duration(api_duration)}) "
                        f"[{completed_count}/{page_count} done, {progress_pct:.0f}%]"
                    )

                    return PageResult(
                        page_number=page_number,
                        content=content,
                        char_count=len(content),
                        api_duration=api_duration,
                        success=True,
                    )

                except Exception as e:
                    page_duration = time.time() - page_start

                    async with completed_lock:
                        completed_count += 1

                    logger.error(
                        f"[GeminiOCR] ✗ Page {page_number} FAILED after "
                        f"{_format_duration(page_duration)}: {e}"
                    )

                    return PageResult(
                        page_number=page_number,
                        content=f"[Error extracting text from page {page_number}]",
                        char_count=0,
                        api_duration=0,
                        success=False,
                        error=str(e),
                    )

        # Create tasks for all pages
        tasks = [process_page_with_progress(i, img) for i, img in enumerate(images)]

        # Execute all tasks in parallel (limited by semaphore)
        ocr_start = time.time()
        results: List[PageResult] = await asyncio.gather(*tasks)
        ocr_duration = time.time() - ocr_start

        # Sort results by page number (they may complete out of order)
        results.sort(key=lambda r: r.page_number)

        # Build ParsedPage list and collect stats
        pages = []
        total_chars = 0
        total_api_time = 0
        successful_pages = 0
        failed_pages = 0

        for result in results:
            if result.success:
                successful_pages += 1
                total_chars += result.char_count
                total_api_time += result.api_duration
            else:
                failed_pages += 1

            pages.append(
                ParsedPage(
                    page_number=result.page_number,
                    content=result.content,
                    has_ocr=True,
                    metadata={
                        "extraction_method": "gemini_vision_parallel",
                        "model": self.model_name,
                        "char_count": result.char_count,
                        "api_duration_ms": int(result.api_duration * 1000),
                        "success": result.success,
                        "error": result.error,
                    },
                )
            )

        # Final summary
        total_duration = time.time() - total_start_time
        avg_time_per_page = total_duration / page_count if page_count > 0 else 0
        speedup = (total_api_time / total_duration) if total_duration > 0 else 1

        logger.info(f"[GeminiOCR] {'─' * 50}")

        # Check for network-related failures
        network_errors = [
            r
            for r in results
            if not r.success
            and r.error
            and (
                "timeout" in r.error.lower()
                or "connect" in r.error.lower()
                or "network" in r.error.lower()
            )
        ]

        if failed_pages > 0:
            logger.warning(f"[GeminiOCR] ⚠️ PARALLEL OCR COMPLETED WITH ERRORS for: {filename}")
        else:
            logger.info(f"[GeminiOCR] 🎉 PARALLEL OCR COMPLETE for: {filename}")

        logger.info(f"[GeminiOCR] {'=' * 60}")
        logger.info(f"[GeminiOCR] Summary:")
        logger.info(f"[GeminiOCR]   • Total pages: {page_count}")
        logger.info(f"[GeminiOCR]   • Successful: {successful_pages} | Failed: {failed_pages}")
        logger.info(f"[GeminiOCR]   • Total characters extracted: {total_chars:,}")
        logger.info(f"[GeminiOCR]   • Workers used: {self.concurrency}")
        logger.info(f"[GeminiOCR]   • Wall time: {_format_duration(total_duration)}")
        logger.info(f"[GeminiOCR]   • OCR phase: {_format_duration(ocr_duration)}")
        logger.info(f"[GeminiOCR]   • Cumulative API time: {_format_duration(total_api_time)}")
        logger.info(
            f"[GeminiOCR]   • Avg wall time per page: {_format_duration(avg_time_per_page)}"
        )
        logger.info(f"[GeminiOCR]   • Parallel speedup: {speedup:.1f}x")

        # Provide guidance if there were network errors
        if network_errors:
            logger.warning(f"[GeminiOCR] {'─' * 50}")
            logger.warning(
                f"[GeminiOCR] ⚠️ {len(network_errors)} pages failed due to network/timeout issues"
            )
            logger.warning(
                "[GeminiOCR] 💡 This indicates connectivity problems to Google's servers."
            )
            logger.warning(
                "[GeminiOCR] 💡 Suggestion: Set OCR_MODE=unstructured in .env for offline OCR"
            )

        logger.info(f"[GeminiOCR] {'=' * 60}")

        return ParseResult(
            pages=pages,
            document_type=DocumentType.PDF,
            metadata={
                "source_file": filename,
                "ocr_model": self.model_name,
                "dpi": self.dpi,
                "concurrency": self.concurrency,
                "total_chars": total_chars,
                "total_duration_ms": int(total_duration * 1000),
                "ocr_duration_ms": int(ocr_duration * 1000),
                "cumulative_api_duration_ms": int(total_api_time * 1000),
                "parallel_speedup": round(speedup, 2),
            },
            page_count=page_count,
            has_ocr=True,
            parser_name=self.parser_name,
        )

    def _extract_text_from_image_sync(
        self, client, image, page_number: int, total_pages: int
    ) -> tuple[str, float]:
        """
        Extract text from a single page image using Gemini (synchronous).

        Includes retry logic with exponential backoff for rate limit errors (429).

        Args:
            client: Gemini GenerativeModel client.
            image: PIL Image object.
            page_number: Page number for logging.
            total_pages: Total number of pages (for context).

        Returns:
            Tuple of (extracted text content, API call duration in seconds).
        """
        # Convert PIL image to bytes for Gemini
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="JPEG", quality=95)
        img_bytes_size = img_byte_arr.tell()
        img_byte_arr.seek(0)

        logger.debug(
            f"[GeminiOCR]   Page {page_number}: Image prepared: {img_bytes_size / 1024:.1f} KB "
            f"({image.width}x{image.height})"
        )

        # Create prompt with page context
        prompt = f"Page {page_number} of {total_pages}:\n\n{self.ocr_prompt}"

        # Retry configuration
        max_retries = 3
        base_delay = 2.0  # Base delay in seconds

        total_api_duration = 0.0
        last_error = None

        # Import request options for timeout
        try:
            from google.generativeai.types import RequestOptions

            request_options = RequestOptions(timeout=self.request_timeout)
        except ImportError:
            request_options = None

        for attempt in range(max_retries + 1):
            try:
                # Send to Gemini and measure API time
                if attempt > 0:
                    logger.info(
                        f"[GeminiOCR]   Page {page_number}: Retry {attempt}/{max_retries}..."
                    )
                else:
                    logger.debug(
                        f"[GeminiOCR]   Page {page_number}: Calling Gemini API "
                        f"(timeout: {self.request_timeout}s)..."
                    )

                api_start = time.time()
                if request_options:
                    response = client.generate_content(
                        [prompt, image],
                        request_options=request_options,
                    )
                else:
                    response = client.generate_content([prompt, image])
                api_duration = time.time() - api_start
                total_api_duration += api_duration

                # Log detailed response information
                self._log_response_details(response, page_number, api_duration)

                # Check for prompt feedback (blocked prompts)
                if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                    feedback = response.prompt_feedback
                    if hasattr(feedback, "block_reason") and feedback.block_reason:
                        block_reason = str(feedback.block_reason)
                        logger.error(
                            f"[GeminiOCR]   ✗ Page {page_number}: Prompt BLOCKED - "
                            f"Reason: {block_reason}"
                        )
                        # Log safety ratings if available
                        if hasattr(feedback, "safety_ratings") and feedback.safety_ratings:
                            for rating in feedback.safety_ratings:
                                logger.error(
                                    f"[GeminiOCR]     Safety: {rating.category} = {rating.probability}"
                                )
                        raise DocumentParsingError(
                            f"Gemini blocked the prompt for page {page_number}: {block_reason}"
                        )

                # Check candidates for finish reason
                if hasattr(response, "candidates") and response.candidates:
                    for idx, candidate in enumerate(response.candidates):
                        finish_reason = getattr(candidate, "finish_reason", None)
                        if finish_reason:
                            finish_reason_str = str(finish_reason)
                            # Log non-STOP finish reasons as warnings
                            if "STOP" not in finish_reason_str:
                                logger.warning(
                                    f"[GeminiOCR]   ⚠️ Page {page_number}: "
                                    f"Candidate {idx} finish_reason: {finish_reason_str}"
                                )

                                # Check for safety-related stops
                                if "SAFETY" in finish_reason_str:
                                    logger.error(
                                        f"[GeminiOCR]   ✗ Page {page_number}: "
                                        f"Response blocked due to SAFETY"
                                    )
                                    # Log safety ratings
                                    if hasattr(candidate, "safety_ratings"):
                                        for rating in candidate.safety_ratings:
                                            logger.error(
                                                f"[GeminiOCR]     Safety: "
                                                f"{rating.category} = {rating.probability}"
                                            )

                # Extract text from response
                try:
                    text = response.text
                    if text:
                        text = text.strip()
                        logger.info(
                            f"[GeminiOCR]   ✓ Page {page_number}: SUCCESS - "
                            f"{len(text):,} chars in {_format_duration(api_duration)}"
                        )
                        return text, total_api_duration
                    else:
                        logger.warning(
                            f"[GeminiOCR]   ⚠️ Page {page_number}: Empty text in response"
                        )
                        return "", total_api_duration
                except ValueError as ve:
                    # response.text raises ValueError if response is blocked
                    logger.error(
                        f"[GeminiOCR]   ✗ Page {page_number}: Cannot access response text - {ve}"
                    )
                    # Try to get more details
                    if hasattr(response, "candidates") and response.candidates:
                        for idx, candidate in enumerate(response.candidates):
                            logger.error(
                                f"[GeminiOCR]     Candidate {idx}: "
                                f"finish_reason={getattr(candidate, 'finish_reason', 'N/A')}"
                            )
                    raise DocumentParsingError(
                        f"Gemini response blocked for page {page_number}: {ve}"
                    )

            except DocumentParsingError:
                # Re-raise our own errors
                raise
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                error_type = type(e).__name__

                # Log full error details
                logger.error(
                    f"[GeminiOCR]   ✗ Page {page_number}: API Exception - "
                    f"Type: {error_type}, Message: {e}"
                )

                # Check if it's a rate limit error (429) or quota exceeded
                is_rate_limit = (
                    "429" in error_str
                    or "rate limit" in error_str
                    or "quota" in error_str
                    or "resource exhausted" in error_str
                    or "too many requests" in error_str
                )

                # Check for server/network errors
                is_server_error = (
                    "500" in error_str
                    or "502" in error_str
                    or "503" in error_str
                    or "504" in error_str
                    or "internal" in error_str
                    or "unavailable" in error_str
                )

                # Check for timeout/connection errors (non-retryable - indicates network issue)
                is_network_error = (
                    "timeout" in error_str
                    or "timed out" in error_str
                    or "connection" in error_str
                    or "connect" in error_str
                    or "failed to connect" in error_str
                    or "retryerror" in error_str
                    or "deadline" in error_str
                )

                # Network errors should fail fast with helpful message
                if is_network_error and attempt >= 1:
                    logger.error(
                        f"[GeminiOCR]   ✗ Page {page_number}: Network connectivity issue detected. "
                        f"Cannot reach Google Gemini API."
                    )
                    logger.error(
                        "[GeminiOCR]   💡 Suggestion: Set OCR_MODE=unstructured to use offline OCR"
                    )
                    raise DocumentParsingError(
                        f"Network connectivity issue: Cannot reach Google Gemini API. "
                        f"Error: {e}\n\n"
                        "This is likely caused by:\n"
                        "  - Network firewall blocking Google services\n"
                        "  - VPN blocking connections\n"
                        "  - Running in a region where Google is blocked\n\n"
                        "Solution: Set OCR_MODE=unstructured in your .env file to use offline OCR."
                    )

                if (is_rate_limit or is_server_error or is_network_error) and attempt < max_retries:
                    # Exponential backoff: 2s, 4s, 8s
                    delay = base_delay * (2**attempt)
                    if is_rate_limit:
                        error_type_msg = "Rate limit"
                    elif is_network_error:
                        error_type_msg = "Network/timeout"
                    else:
                        error_type_msg = "Server error"
                    logger.warning(
                        f"[GeminiOCR]   ⚠️ Page {page_number}: {error_type_msg} hit, "
                        f"waiting {delay:.1f}s before retry {attempt + 1}/{max_retries}..."
                    )
                    time.sleep(delay)
                    continue
                elif is_rate_limit or is_server_error:
                    logger.error(
                        f"[GeminiOCR]   ✗ Page {page_number}: Failed after "
                        f"{max_retries} retries: {error_type}: {e}"
                    )
                    raise
                else:
                    # Non-retryable error
                    logger.error(
                        f"[GeminiOCR]   ✗ Page {page_number}: Non-retryable error: "
                        f"{error_type}: {e}"
                    )
                    raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        return "", total_api_duration

    def _log_response_details(self, response, page_number: int, api_duration: float):
        """Log detailed information about the Gemini API response."""
        try:
            # Log basic response info
            logger.debug(
                f"[GeminiOCR]   Page {page_number}: Response received in "
                f"{_format_duration(api_duration)}"
            )

            # Log prompt feedback if present
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                feedback = response.prompt_feedback
                logger.debug(f"[GeminiOCR]   Page {page_number}: Prompt feedback: {feedback}")

            # Log candidate count
            if hasattr(response, "candidates"):
                num_candidates = len(response.candidates) if response.candidates else 0
                logger.debug(f"[GeminiOCR]   Page {page_number}: {num_candidates} candidate(s)")

                # Log each candidate's details
                for idx, candidate in enumerate(response.candidates or []):
                    finish_reason = getattr(candidate, "finish_reason", "N/A")
                    logger.debug(
                        f"[GeminiOCR]   Page {page_number}: "
                        f"Candidate {idx} finish_reason: {finish_reason}"
                    )

                    # Log safety ratings at debug level
                    if hasattr(candidate, "safety_ratings") and candidate.safety_ratings:
                        for rating in candidate.safety_ratings:
                            cat = getattr(rating, "category", "N/A")
                            prob = getattr(rating, "probability", "N/A")
                            # Only log if probability is not NEGLIGIBLE
                            if "NEGLIGIBLE" not in str(prob):
                                logger.debug(
                                    f"[GeminiOCR]   Page {page_number}: Safety {cat}: {prob}"
                                )

            # Log usage metadata if available
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = response.usage_metadata
                prompt_tokens = getattr(usage, "prompt_token_count", "N/A")
                output_tokens = getattr(usage, "candidates_token_count", "N/A")
                logger.debug(
                    f"[GeminiOCR]   Page {page_number}: "
                    f"Tokens - prompt: {prompt_tokens}, output: {output_tokens}"
                )

        except Exception as e:
            # Don't let logging errors break the main flow
            logger.debug(f"[GeminiOCR]   Page {page_number}: Error logging details: {e}")
