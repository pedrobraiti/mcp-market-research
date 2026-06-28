"""Shared note-building for the multi-symbol aggregators.

A per-symbol read in a batch (classify/compare/calendar/news_digest) can fail two very different
ways, and collapsing them into one ``"unavailable"`` blinds the caller to the right next move:

* a **transient** exception (429/timeout) is "couldn't fetch" → the loop should retry or abstain;
* a genuine ``None`` is "fetched, no such thing" → ``not_found`` → don't bother retrying.

So callers branch on a machine-readable note instead of guessing from a vague string.
"""

from __future__ import annotations

from ..adapters.retry import unavailable_status

NOT_FOUND = "not_found"


def unavailable_or_not_found(result: object) -> str:
    """Note for a failed per-symbol read: a reason-tagged ``unavailable: …`` for an exception
    (transient or otherwise), or ``not_found`` for a genuine ``None``."""
    if isinstance(result, Exception):
        return unavailable_status(result)
    return NOT_FOUND
