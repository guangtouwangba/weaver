"""Unit tests for URL extractor module."""


from research_agent.infrastructure.url_extractor.utils import (
    detect_platform,
    normalize_url,
    validate_url,
)


class TestUrlValidation:
    """Tests for URL validation."""

    def test_valid_http_url(self):
        is_valid, error = validate_url("http://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_https_url(self):
        is_valid, error = validate_url("https://example.com/path?query=1")
        assert is_valid is True
        assert error is None

    def test_empty_url(self):
        is_valid, error = validate_url("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_invalid_scheme(self):
        is_valid, error = validate_url("ftp://example.com")
        assert is_valid is False
        assert "scheme" in error.lower()

    def test_missing_domain(self):
        is_valid, error = validate_url("https://")
        assert is_valid is False
        assert "domain" in error.lower()

    def test_url_too_long(self):
        long_url = "https://example.com/" + "a" * 2100
        is_valid, error = validate_url(long_url)
        assert is_valid is False
        assert "long" in error.lower()


class TestPlatformDetection:
    """Tests for platform detection."""

    # YouTube tests
    def test_youtube_standard_watch(self):
        platform, video_id = detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert platform == "youtube"
        assert video_id == "dQw4w9WgXcQ"

    def test_youtube_short_url(self):
        platform, video_id = detect_platform("https://youtu.be/dQw4w9WgXcQ")
        assert platform == "youtube"
        assert video_id == "dQw4w9WgXcQ"

    def test_youtube_shorts(self):
        platform, video_id = detect_platform("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        assert platform == "youtube"
        assert video_id == "dQw4w9WgXcQ"

    def test_youtube_embed(self):
        platform, video_id = detect_platform("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert platform == "youtube"
        assert video_id == "dQw4w9WgXcQ"

    def test_youtube_without_www(self):
        platform, video_id = detect_platform("https://youtube.com/watch?v=dQw4w9WgXcQ")
        assert platform == "youtube"
        assert video_id == "dQw4w9WgXcQ"

    # Bilibili tests
    def test_bilibili_standard_bv(self):
        platform, video_id = detect_platform("https://www.bilibili.com/video/BV1GJ411x7h7")
        assert platform == "bilibili"
        assert video_id == "BV1GJ411x7h7"

    def test_bilibili_without_www(self):
        platform, video_id = detect_platform("https://bilibili.com/video/BV1GJ411x7h7")
        assert platform == "bilibili"
        assert video_id == "BV1GJ411x7h7"

    def test_bilibili_short_url(self):
        platform, video_id = detect_platform("https://b23.tv/BV1GJ411x7h7")
        assert platform == "bilibili"
        assert video_id == "BV1GJ411x7h7"

    # Douyin tests
    def test_douyin_standard(self):
        platform, video_id = detect_platform("https://www.douyin.com/video/7123456789012345678")
        assert platform == "douyin"
        assert video_id == "7123456789012345678"

    def test_douyin_short_url(self):
        platform, video_id = detect_platform("https://v.douyin.com/abc123")
        assert platform == "douyin"
        assert video_id == "abc123"

    # Generic web tests
    def test_generic_web_page(self):
        platform, video_id = detect_platform("https://example.com/article/123")
        assert platform == "web"
        assert video_id is None

    def test_generic_blog(self):
        platform, video_id = detect_platform("https://blog.example.org/post/hello-world")
        assert platform == "web"
        assert video_id is None


class TestUrlNormalization:
    """Tests for URL normalization."""

    def test_removes_tracking_params(self):
        url = "https://example.com/page?utm_source=twitter&utm_medium=social&id=123"
        normalized = normalize_url(url)
        assert "utm_source" not in normalized
        assert "utm_medium" not in normalized
        assert "id=123" in normalized

    def test_removes_www(self):
        url = "https://www.example.com/page"
        normalized = normalize_url(url)
        assert normalized == "https://example.com/page"

    def test_lowercase_scheme_and_domain(self):
        url = "HTTPS://WWW.EXAMPLE.COM/Page"
        normalized = normalize_url(url)
        assert normalized.startswith("https://example.com")

    def test_normalizes_youtube_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        normalized = normalize_url(url)
        assert normalized == "https://youtube.com/watch?v=dQw4w9WgXcQ"

    def test_normalizes_youtube_with_tracking(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&utm_source=twitter"
        normalized = normalize_url(url)
        assert normalized == "https://youtube.com/watch?v=dQw4w9WgXcQ"

    def test_removes_trailing_slash(self):
        url = "https://example.com/page/"
        normalized = normalize_url(url)
        assert not normalized.endswith("/page/")
        assert "/page" in normalized

    def test_preserves_necessary_params(self):
        url = "https://example.com/search?q=hello&page=2"
        normalized = normalize_url(url)
        assert "q=hello" in normalized
        assert "page=2" in normalized

