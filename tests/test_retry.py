import pytest

from scout.adapters.retry import SourceUnavailable, classify_transient, with_retry


class _Resp:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class _HttpError(Exception):
    def __init__(self, status_code: int) -> None:
        self.response = _Resp(status_code)
        super().__init__(f"HTTP {status_code}")


class _ReadTimeout(Exception):
    """Name contains 'timeout' so the classifier treats it as transient (like httpx.ReadTimeout)."""


def test_classify_detects_429_and_5xx_as_rate_limited():
    assert classify_transient(_HttpError(429)) == "rate_limited"
    assert classify_transient(_HttpError(503)) == "rate_limited"


def test_classify_detects_timeout_by_name():
    assert classify_transient(_ReadTimeout()) == "timeout"


def test_classify_ignores_non_transient():
    assert classify_transient(_HttpError(404)) is None
    assert classify_transient(ValueError("bad payload")) is None


async def test_with_retry_returns_value_without_retrying():
    calls = {"n": 0}

    async def op():
        calls["n"] += 1
        return "ok"

    assert await with_retry(op, attempts=3, base_delay=0) == "ok"
    assert calls["n"] == 1


async def test_with_retry_recovers_after_transient_failures():
    calls = {"n": 0}

    async def op():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _HttpError(429)
        return "recovered"

    assert await with_retry(op, attempts=3, base_delay=0) == "recovered"
    assert calls["n"] == 3


async def test_with_retry_raises_source_unavailable_after_exhaustion():
    calls = {"n": 0}

    async def op():
        calls["n"] += 1
        raise _ReadTimeout()

    with pytest.raises(SourceUnavailable) as exc_info:
        await with_retry(op, attempts=2, base_delay=0)
    assert calls["n"] == 2
    assert exc_info.value.reason == "timeout"
    assert exc_info.value.status == "unavailable: timeout"


async def test_with_retry_reraises_non_transient_immediately():
    calls = {"n": 0}

    async def op():
        calls["n"] += 1
        raise ValueError("genuine error")

    with pytest.raises(ValueError, match="genuine error"):
        await with_retry(op, attempts=5, base_delay=0)
    assert calls["n"] == 1  # not retried
