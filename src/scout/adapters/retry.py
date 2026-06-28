"""Shared HTTP retry/backoff for the keyless web adapters (GDELT, FRED, …).

The free data sources rate-limit (HTTP 429) and occasionally time out. A null field coming
from a rate-limit must NOT look like "this data does not exist" — that would mislead a
downstream data-sufficiency gate. So this helper retries transient failures (429 and connect/
read timeouts) with exponential backoff and, once exhausted, raises ``SourceUnavailable`` with a
machine-readable ``reason`` the adapter surfaces as a status (e.g. ``unavailable: rate_limited``)
instead of a silent ``None``.

Non-transient errors (a 404, a malformed payload, …) propagate immediately — they are genuine,
not worth retrying, and keep the existing error-envelope behaviour.

httpx is intentionally NOT imported here: failures are classified structurally (a ``response``
with ``status_code``) and by exception-class name, so offline tests can simulate a 429/timeout
with a tiny fake and never need the network.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

RATE_LIMITED = "rate_limited"
TIMEOUT = "timeout"

# 429 plus the transient-overload 5xx family — all worth backing off and retrying.
_RETRYABLE_STATUS = {429, 502, 503, 504}


class SourceUnavailable(Exception):
    """A source could not be reached after retries — 'couldn't fetch', not 'fetched, empty'.

    ``reason`` is machine-readable (``rate_limited`` / ``timeout``); ``status`` is the ready-made
    label adapters attach to a model so the caller can tell the two apart.
    """

    def __init__(self, reason: str, message: str | None = None) -> None:
        self.reason = reason
        self.status = f"unavailable: {reason}"
        super().__init__(message or self.status)


def classify_transient(exc: Exception) -> str | None:
    """Return a retry reason for a transient HTTP failure, else ``None`` (do not retry)."""
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code in _RETRYABLE_STATUS:
        return RATE_LIMITED
    if "timeout" in type(exc).__name__.lower():
        return TIMEOUT
    return None


async def with_retry[T](
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
) -> T:
    """Run an async fetch, retrying 429/timeout with exponential backoff.

    Succeeds → returns the value. Transient failure that persists past ``attempts`` →
    ``SourceUnavailable``. Any other exception is re-raised untouched on first sight.
    """
    bounded_attempts = max(1, attempts)
    last_reason: str | None = None
    last_error: Exception | None = None
    for attempt in range(bounded_attempts):
        try:
            return await operation()
        except SourceUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001 — classify, then retry-or-reraise
            reason = classify_transient(exc)
            if reason is None:
                raise
            last_reason, last_error = reason, exc
            if attempt < bounded_attempts - 1 and base_delay > 0:
                await sleep(base_delay * (2**attempt))
    raise SourceUnavailable(last_reason or RATE_LIMITED) from last_error
