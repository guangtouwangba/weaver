"""
Fixtures and configuration specific to file loader tests.
"""

import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

import pytest
from modules.file_loader.pdf.pdf_loader import PDFFileLoader
from modules.models import FileLoadRequest
from modules.schemas.enums import ContentType


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def pdf_loader_config() -> Dict[str, Any]:
    """Configuration for PDF loader tests"""
    return {
        "max_file_size": 50 * 1024 * 1024,  # 50MB
        "test_timeout": 30,  # seconds
        "mock_page_count": 5,
        "mock_content_length": 1000,
    }


@pytest.fixture
def real_pdf_file_path():
    return Path(
        __file__).parent.parent.parent / "test_files" / "用户故事地图 (JEFF PATTON著) (Z-Library).pdf"


@pytest.fixture
def mock_pdf_file_path(temp_dir):
    """Create a mock PDF file path for testing"""
    mock_pdf = temp_dir / "mock_test.pdf"
    mock_pdf.write_bytes(b"%PDF-1.4\n%Mock PDF content for testing\n%%EOF")
    return mock_pdf


@pytest.fixture
def real_file_load_request(real_pdf_file_path):
    """Real FileLoadRequest using actual PDF"""
    return FileLoadRequest(file_path=str(real_pdf_file_path))

@pytest.fixture
def pdf_mock_factories():
    """Factory functions for creating PDF library mocks"""

    class MockFactories:
        @staticmethod
        def create_fitz_mock(pages_content: list, metadata: Dict[str, Any] = None):
            """Create mock fitz document"""
            # TODO: Implement fitz mock factory
            mock_doc = Mock()
            mock_pages = []

            for i, content in enumerate(pages_content):
                mock_page = Mock()
                mock_page.get_text.return_value = content
                mock_pages.append(mock_page)

            mock_doc.__len__.return_value = len(pages_content)
            mock_doc.load_page.side_effect = lambda i: mock_pages[i]
            mock_doc.metadata = metadata or {}
            mock_doc.close.return_value = None

            return mock_doc

        @staticmethod
        def create_pypdf2_mock(pages_content: list, metadata: Dict[str, Any] = None):
            """Create mock PyPDF2 reader"""
            # TODO: Implement PyPDF2 mock factory
            mock_reader = Mock()
            mock_pages = []

            for content in pages_content:
                mock_page = Mock()
                mock_page.extract_text.return_value = content
                mock_pages.append(mock_page)

            mock_reader.pages = mock_pages
            mock_reader.metadata = metadata or {}

            return mock_reader

    return MockFactories()


@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing"""
    return {
        "file_not_found": {
            "file_path": "/nonexistent/path/file.pdf",
            "expected_error": FileNotFoundError,
            "error_message": "file does not exist"
        },
        "file_too_large": {
            "file_size": 200 * 1024 * 1024,  # 200MB
            "max_size": 100 * 1024 * 1024,  # 100MB limit
            "expected_error": "file too large"
        },
        "invalid_format": {
            "file_extension": ".txt",
            "expected_error": "Unsupported file format"
        },
        "corrupted_pdf": {
            "corruption_type": "invalid_header",
            "expected_error": "PDF format validation failed"
        },
        "extraction_failure": {
            "library_error": Exception("Mock extraction error"),
            "expected_error": "PDF content extraction failed"
        }
    }


@pytest.fixture
def performance_test_data():
    """Data for performance testing scenarios"""
    return {
        "large_content": "A" * 10000,  # 10KB of content per page
        "many_pages": 100,
        "concurrent_requests": 10,
        "timeout_seconds": 5,
    }


# Custom pytest markers for file loader tests
def pytest_configure(config):
    """Configure custom markers for file loader tests"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "file_loader: mark test as file loader test")
    config.addinivalue_line("markers", "pdf_loader: mark test as PDF loader test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_pdf_lib: mark test as requiring PDF libraries")


# Test data for parameterized tests
LIBRARY_COMBINATIONS = [
    pytest.param(True, False, id="pymupdf_only"),
    pytest.param(False, True, id="pypdf2_only"),
    pytest.param(True, True, id="both_libraries"),
    pytest.param(False, False, id="no_libraries"),
]

FILE_SIZE_TEST_CASES = [
    (1024, True),  # 1KB - valid
    (1024 * 1024, True),  # 1MB - valid
    (50 * 1024 * 1024, True),  # 50MB - valid (at limit)
    (100 * 1024 * 1024, False),  # 100MB - too large
    (200 * 1024 * 1024, False),  # 200MB - too large
]

CONTENT_TYPE_TEST_CASES = [
    (ContentType.PDF, True),
    (ContentType.TXT, False),
    (ContentType.DOC, False),
    (ContentType.HTML, False),
]
