"""Utility functions for URL extraction."""

import ipaddress
import re
import socket
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from research_agent.config import get_settings

# Platform detection patterns
PLATFORM_PATTERNS = {
    "youtube": [
        # Standard watch URL: youtube.com/watch?v=VIDEO_ID
        r"(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        # Short URL: youtu.be/VIDEO_ID
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        # Shorts: youtube.com/shorts/VIDEO_ID
        r"(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
        # Embed: youtube.com/embed/VIDEO_ID
        r"(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    ],
    "bilibili": [
        # Standard video: bilibili.com/video/BVxxxxx
        r"(?:www\.)?bilibili\.com/video/(BV[a-zA-Z0-9]+)",
        # Short URL: b23.tv/xxxxx
        r"b23\.tv/([a-zA-Z0-9]+)",
    ],
    "douyin": [
        # Standard video: douyin.com/video/VIDEO_ID
        r"(?:www\.)?douyin\.com/video/(\d+)",
        # Short URL: v.douyin.com/xxxxx
        r"v\.douyin\.com/([a-zA-Z0-9]+)",
    ],
}

# Tracking parameters to remove during normalization
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
    "source",
    "share_source",
    "share_medium",
    "spm_id_from",
    "from_source",
    "share_token",
    "timestamp",
    "t",  # YouTube timestamp (optional to keep)
    "feature",
    "app",
}


def validate_url(url: str) -> tuple[bool, str | None]:
    """
    Validate a URL and perform SSRF checks.

    Args:
        url: The URL to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not url:
        return False, "URL is empty"

    # Check for valid scheme
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid URL scheme: {parsed.scheme}. Only http and https are supported."

    # Check for valid netloc (domain)
    if not parsed.netloc:
        return False, "Invalid URL: missing domain"

    # Basic length check
    if len(url) > 2048:
        return False, "URL is too long (max 2048 characters)"

    # Check if SSRF protection is disabled (for development/testing)
    settings = get_settings()
    if settings.disable_ssrf_check:
        print(f"[URL Validation] SSRF check disabled, allowing URL: {url}")
        return True, None

    # SSRF Protection: Check for private IPs
    try:
        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL: missing hostname"

        # Remove brackets from IPv6
        if hostname.startswith("[") and hostname.endswith("]"):
            hostname = hostname[1:-1]

        # Resolve hostname to IP
        try:
            ip_address = socket.gethostbyname(hostname)
        except socket.gaierror:
            return False, f"Could not resolve hostname: {hostname}"

        # Check if IP is private or loopback
        ip = ipaddress.ip_address(ip_address)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False, f"Access to private/local network resources is denied: {ip}"

        # Additional check for 0.0.0.0
        if str(ip) == "0.0.0.0":
            return False, "Access to 0.0.0.0 is denied"

    except ValueError:
        return False, "Invalid IP address format"
    except Exception as e:
        return False, f"URL validation failed: {str(e)}"

    return True, None


def detect_platform(url: str) -> tuple[str, str | None]:
    """
    Detect the platform from a URL.

    Args:
        url: The URL to analyze.

    Returns:
        Tuple of (platform, video_id).
        Platform is one of: youtube, bilibili, douyin, web.
        video_id is extracted if available, None otherwise.
    """
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                video_id = match.group(1)
                return platform, video_id

    return "web", None


def normalize_url(url: str) -> str:
    """
    Normalize a URL for deduplication.

    - Remove tracking parameters
    - Normalize domain variants (e.g., youtu.be -> youtube.com)
    - Convert to lowercase scheme and domain
    - Remove trailing slashes

    Args:
        url: The URL to normalize.

    Returns:
        Normalized URL string.
    """
    parsed = urlparse(url)

    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Remove www. prefix for consistency
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # Normalize YouTube short URLs to standard format
    platform, video_id = detect_platform(url)
    if platform == "youtube" and video_id:
        return f"https://youtube.com/watch?v={video_id}"

    # Normalize Bilibili short URLs
    if platform == "bilibili" and video_id and video_id.startswith("BV"):
        return f"https://bilibili.com/video/{video_id}"

    # Parse and filter query parameters
    query_params = parse_qs(parsed.query, keep_blank_values=False)

    # Remove tracking parameters
    filtered_params = {k: v for k, v in query_params.items() if k.lower() not in TRACKING_PARAMS}

    # Rebuild query string
    new_query = urlencode(filtered_params, doseq=True) if filtered_params else ""

    # Remove trailing slash from path
    path = parsed.path.rstrip("/") or "/"

    # Reconstruct URL
    normalized = urlunparse((scheme, netloc, path, parsed.params, new_query, ""))

    return normalized


def extract_video_id(url: str, platform: str) -> str | None:
    """
    Extract video ID from a URL for a specific platform.

    Args:
        url: The URL to extract from.
        platform: The platform identifier.

    Returns:
        Video ID if found, None otherwise.
    """
    if platform not in PLATFORM_PATTERNS:
        return None

    for pattern in PLATFORM_PATTERNS[platform]:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def truncate_content(content: str, max_length: int = 50000) -> str:
    """
    Truncate content to maximum length while preserving word boundaries.

    Args:
        content: The content to truncate.
        max_length: Maximum number of characters.

    Returns:
        Truncated content.
    """
    if not content or len(content) <= max_length:
        return content

    # Find the last space before the limit
    truncated = content[:max_length]
    last_space = truncated.rfind(" ")

    if last_space > max_length * 0.8:  # Only use space if it's reasonably close
        truncated = truncated[:last_space]

    return truncated + "..."
