import pytest
from unittest.mock import patch, MagicMock
from research_agent.infrastructure.url_extractor.handlers.webpage import WebPageExtractor

@pytest.mark.asyncio
class TestWebPageExtractorSSRF:

    async def test_ssrf_prevention_private_ip(self):
        """Test that access to private IP addresses is blocked."""
        extractor = WebPageExtractor()
        url = "http://192.168.1.1/config"

        # Mock trafilatura to verify it is NOT called
        with patch("trafilatura.fetch_url") as mock_fetch:
            # We don't need to mock socket here because 192.168.1.1 is already an IP
            # and validate_url handles IPs directly too (via ipaddress.ip_address)

            result = await extractor.extract(url)

            # Assert failure
            assert result.success is False
            assert result.error is not None
            assert "private" in result.error.lower() or "denied" in result.error.lower()

            # Assert trafilatura was NOT called
            mock_fetch.assert_not_called()

    async def test_ssrf_prevention_localhost(self):
        """Test that access to localhost is blocked."""
        extractor = WebPageExtractor()
        url = "http://localhost:8000"

        with patch("trafilatura.fetch_url") as mock_fetch, \
             patch("socket.gethostbyname") as mock_dns:

            # Mock DNS to resolve localhost to 127.0.0.1
            mock_dns.return_value = "127.0.0.1"

            result = await extractor.extract(url)

            assert result.success is False
            assert "private" in result.error.lower() or "denied" in result.error.lower()
            mock_fetch.assert_not_called()

    async def test_valid_url_allowed(self):
        """Test that a valid public URL is allowed."""
        extractor = WebPageExtractor()
        url = "http://example.com/article"

        with patch("trafilatura.fetch_url") as mock_fetch, \
             patch("trafilatura.extract") as mock_extract, \
             patch("socket.gethostbyname") as mock_dns:

            # Mock DNS to resolve to a public IP
            mock_dns.return_value = "93.184.216.34" # example.com

            # Mock content
            mock_fetch.return_value = "<html><body><h1>Title</h1><p>Content</p></body></html>"
            mock_extract.side_effect = ["Content", '{"title": "Title"}'] # Content, then Metadata

            result = await extractor.extract(url)

            assert result.success is True
            # Verification that fetch WAS called
            mock_fetch.assert_called_once()
