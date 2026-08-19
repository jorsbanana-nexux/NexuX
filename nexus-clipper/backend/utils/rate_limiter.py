"""
NexuX V8.0 — Rate Limiter (Token Bucket)

Configurable per-endpoint rate limiting using in-memory token buckets.
Returns 429 with Retry-After header when exceeded.
"""

import time
from collections import defaultdict
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


class TokenBucket:
    """Simple token bucket rate limiter."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def consume(self, tokens: int = 1) -> tuple[bool, float]:
        """Try to consume tokens. Returns (allowed, retry_after_seconds)."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, 0.0
        else:
            needed = tokens - self.tokens
            retry_after = needed / self.refill_rate
            return False, retry_after


class RateLimiter:
    """Per-IP/API-key rate limiter with configurable limits per endpoint group."""

    def __init__(self):
        self._buckets: dict[str, dict[str, TokenBucket]] = defaultdict(dict)
        # Default limits: (capacity, refill_rate_per_second)
        self._limits = {
            "generate": (5, 5 / 60),     # 5 requests per minute
            "search": (10, 10 / 60),     # 10 requests per minute
            "preview": (10, 10 / 60),    # 10 requests per minute
            "default": (30, 30 / 60),    # 30 requests per minute
        }

    def get_key(self, request: Request) -> str:
        """Get rate limit key from API key or client IP."""
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            return f"key:{api_key}"
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        return f"ip:{request.client.host if request.client else 'unknown'}"

    def check(self, request: Request, group: str = "default") -> Optional[JSONResponse]:
        """Check rate limit. Returns None if allowed, or 429 response if exceeded."""
        limits = self._limits.get(group, self._limits["default"])
        capacity, refill_rate = limits
        key = self.get_key(request)

        if key not in self._buckets[group]:
            self._buckets[group][key] = TokenBucket(capacity, refill_rate)

        bucket = self._buckets[group][key]
        allowed, retry_after = bucket.consume()

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "retry_after": round(retry_after, 1)},
                headers={"Retry-After": str(int(retry_after) + 1)},
            )
        return None

    def configure(self, group: str, capacity: int, refill_per_minute: float):
        """Configure limits for a specific group."""
        self._limits[group] = (capacity, refill_per_minute / 60)
        self._buckets[group].clear()


# Global rate limiter instance
rate_limiter = RateLimiter()
