"""Token estimation service for different languages and content types."""

import re
from functools import lru_cache
from typing import Literal

# Token estimation ratios (characters per token)
TOKEN_RATIOS = {
    "chinese": 1.5,  # 1 token ≈ 1.5 Chinese characters
    "english": 4.0,  # 1 token ≈ 4 English characters
    "code": 3.0,  # 1 token ≈ 3 code characters
    "mixed": 2.5,  # 1 token ≈ 2.5 characters (default for mixed content)
}


class TokenEstimator:
    """Service for estimating token counts in text."""

    @staticmethod
    def detect_language(text: str) -> Literal["chinese", "english", "code", "mixed"]:
        """
        Detect the primary language/content type of text.

        Args:
            text: Text to analyze

        Returns:
            Detected language type
        """
        # Check for code patterns
        code_patterns = [
            r"def\s+\w+\s*\(",
            r"function\s+\w+\s*\(",
            r"class\s+\w+",
            r"import\s+\w+",
            r"#include",
            r"<\w+>",
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in code_patterns):
            return "code"

        # Count Chinese characters
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        total_chars = len(text.replace(" ", "").replace("\n", ""))

        if total_chars == 0:
            return "mixed"

        chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0

        # If more than 50% Chinese characters, consider it Chinese
        if chinese_ratio > 0.5:
            return "chinese"

        # If more than 80% English (ASCII), consider it English
        ascii_chars = len(re.findall(r"[a-zA-Z]", text))
        ascii_ratio = ascii_chars / total_chars if total_chars > 0 else 0
        if ascii_ratio > 0.8:
            return "english"

        # Default to mixed
        return "mixed"

    @staticmethod
    def estimate_tokens(text: str, language: str | None = None) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to estimate
            language: Language type (chinese, english, code, mixed). If None, auto-detect.

        Returns:
            Estimated token count
        """
        if not text or not text.strip():
            return 0

        # Auto-detect language if not provided
        if language is None:
            language = TokenEstimator.detect_language(text)

        # Get token ratio
        ratio = TOKEN_RATIOS.get(language, TOKEN_RATIOS["mixed"])

        # Count non-whitespace characters
        char_count = len(text.replace(" ", "").replace("\n", ""))

        # Estimate tokens
        tokens = int(char_count / ratio)

        # Minimum 1 token for non-empty text
        return max(1, tokens)

    @staticmethod
    @lru_cache(maxsize=1000)
    def estimate_document_tokens(content: str) -> int:
        """
        Estimate token count for a document (with caching).

        Args:
            content: Document content

        Returns:
            Estimated token count
        """
        return TokenEstimator.estimate_tokens(content)


