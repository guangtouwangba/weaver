"""YouTube API retry strategy with exponential backoff."""

import asyncio
import random
from collections.abc import Callable
from typing import TypeVar

from research_agent.shared.utils.logger import logger

T = TypeVar("T")


class YouTubeRateLimiter:
    """Rate limiter for YouTube API calls to avoid IP bans."""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 60.0):
        """Initialize rate limiter.

        Args:
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay for exponential backoff (seconds)
        """
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._last_request_time: float | None = None
        self._consecutive_failures = 0
        self._lock = asyncio.Lock()

    async def execute_with_retry(
        self,
        func: Callable[[], T],
        max_retries: int = 3,
        operation_name: str = "YouTube API call",
    ) -> tuple[T | None, bool]:
        """Execute a function with rate limiting and retry logic.

        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            operation_name: Name of the operation for logging

        Returns:
            Tuple of (result, success)
        """
        async with self._lock:
            for attempt in range(max_retries + 1):
                # Apply rate limiting delay
                if self._last_request_time is not None:
                    delay = self._calculate_delay()
                    if delay > 0:
                        logger.debug(
                            f"[YouTubeRateLimiter] Waiting {delay:.1f}s before {operation_name}"
                        )
                        await asyncio.sleep(delay)

                try:
                    # Execute the function
                    # import asyncio # Removed inner import to fix F823
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, func)

                    # Success - reset failure counter
                    self._consecutive_failures = 0
                    self._last_request_time = asyncio.get_event_loop().time()

                    return result, True

                except Exception as e:
                    error_str = str(e)
                    is_rate_limit = any(
                        keyword in error_str
                        for keyword in [
                            "RequestBlocked",
                            "IpBlocked",
                            "blocking requests",
                            "Too Many Requests",
                            "429",
                        ]
                    )

                    if is_rate_limit:
                        self._consecutive_failures += 1

                        if attempt < max_retries:
                            backoff_delay = self._calculate_backoff_delay(attempt)
                            logger.warning(
                                f"[YouTubeRateLimiter] Rate limit hit for {operation_name}, "
                                f"retrying in {backoff_delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                            )
                            await asyncio.sleep(backoff_delay)
                        else:
                            logger.error(
                                f"[YouTubeRateLimiter] Max retries reached for {operation_name}"
                            )
                            return None, False
                    else:
                        # Non-rate-limit error, don't retry
                        logger.debug(
                            f"[YouTubeRateLimiter] Non-rate-limit error for {operation_name}: {e}"
                        )
                        return None, False

                finally:
                    self._last_request_time = asyncio.get_event_loop().time()

            return None, False

    def _calculate_delay(self) -> float:
        """Calculate delay based on consecutive failures."""
        if self._last_request_time is None:
            return 0.0

        # Base delay increases with consecutive failures
        base_delay = self._min_delay * (1.5 ** self._consecutive_failures)
        base_delay = min(base_delay, self._max_delay)

        # Add jitter to avoid thundering herd
        jitter = random.uniform(0, base_delay * 0.3)

        elapsed = asyncio.get_event_loop().time() - self._last_request_time
        remaining = base_delay + jitter - elapsed

        return max(0.0, remaining)

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay for retries."""
        # Exponential backoff: 2^attempt * base_delay
        delay = (2 ** attempt) * self._min_delay
        delay = min(delay, self._max_delay)

        # Add jitter
        jitter = random.uniform(0, delay * 0.3)

        return delay + jitter


# Global rate limiter instance
_rate_limiter = YouTubeRateLimiter(min_delay=2.0, max_delay=60.0)


async def execute_youtube_api_call[T](
    func: Callable[[], T],
    operation_name: str = "YouTube API call",
    max_retries: int = 3,
) -> tuple[T | None, bool]:
    """Execute a YouTube API call with rate limiting and retry logic.

    This is a convenience function that uses the global rate limiter.

    Args:
        func: Function to execute
        operation_name: Name of the operation for logging
        max_retries: Maximum number of retry attempts

    Returns:
        Tuple of (result, success)
    """
    return await _rate_limiter.execute_with_retry(
        func=func,
        max_retries=max_retries,
        operation_name=operation_name,
    )
