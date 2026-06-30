"""openFDA implementation of ``FdaSource`` — keyless drug approvals + recalls.

openFDA exposes FDA drug data with no API key (an optional free key only raises rate limits — it
is NOT required). Two endpoints are composed for one ``fda_events`` answer:

- ``/drug/drugsfda.json?search=sponsor_name:"<NAME>"`` — applications; an APPROVAL is a
  ``submissions`` entry whose ``submission_status == "AP"`` (date in ``submission_status_date``,
  YYYYMMDD). Brand names come from each application's ``products[].brand_name``.
- ``/drug/enforcement.json?search=recalling_firm:"<NAME>"`` — recalls (product, reason,
  classification = severity, status).

The caller passes the ISSUER/SPONSOR NAME (e.g. from ``company_dossier``); name→sponsor-of-record
is fuzzy and out of scope.

Honesty (ADR-012): openFDA returns **HTTP 404 with ``{"error":{"code":"NOT_FOUND"}}`` when a query
has ZERO matches** — that is an empty result (a ``note``), NOT a source failure. A 429/timeout/5xx
IS a failure → ``SourceUnavailable`` → ``unavailable: <reason>``. The two legs fail independently:
a throttled leg sets ``source_status`` and returns empty while the other still returns. The JSON
fetch is injected for offline tests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date, datetime
from typing import Any
from urllib.parse import quote

from ...domain.models import FdaApproval, FdaEvents, FdaRecall
from ..retry import SourceUnavailable, unavailable_status, with_retry

_DRUGSFDA_URL = (
    'https://api.fda.gov/drug/drugsfda.json?search=sponsor_name:"{name}"&limit={limit}'
)
_ENFORCEMENT_URL = (
    'https://api.fda.gov/drug/enforcement.json?search=recalling_firm:"{name}"'
    "&limit={limit}&sort=report_date:desc"
)
_APPROVED = "AP"
_MAX_LIMIT = 100


def _parse_fda_date(value: Any) -> date | None:
    """openFDA dates are YYYYMMDD strings (occasionally YYYY-MM-DD)."""
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10] if "-" in text else text[:8], fmt).date()
        except ValueError:
            continue
    return None


def _is_not_found(payload: Any) -> bool:
    """openFDA's zero-match 404 body: ``{"error":{"code":"NOT_FOUND"}}``."""
    if not isinstance(payload, dict):
        return False
    error = payload.get("error")
    return isinstance(error, dict) and error.get("code") == "NOT_FOUND"


class OpenFdaEvents:
    def __init__(
        self,
        fetch_json: Callable[[str], Awaitable[Any]] | None = None,
        timeout: float = 15.0,
        retry_attempts: int = 3,
        retry_base_delay: float = 0.5,
    ) -> None:
        self._timeout = timeout
        self._retry_attempts = retry_attempts
        self._retry_base_delay = retry_base_delay
        self._fetch_json = fetch_json or self._default_fetch_json

    async def _default_fetch_json(self, url: str) -> Any:
        import httpx

        headers = {"User-Agent": "scout-mcp/0.1 (research; +https://github.com/pedrobraiti)"}
        async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
            response = await client.get(url)
            # A 404 is openFDA's "zero matches" — return its JSON body so the adapter treats it as
            # an empty result, NOT a failure. 429/5xx still raise (→ with_retry classifies them).
            if response.status_code == 404:
                if response.text.strip():
                    return response.json()
                return {"error": {"code": "NOT_FOUND"}}
            response.raise_for_status()
            if not response.text.strip():
                return {}
            return response.json()

    async def _fetch(self, url: str) -> Any:
        return await with_retry(
            lambda: self._fetch_json(url),
            attempts=self._retry_attempts,
            base_delay=self._retry_base_delay,
        )

    async def get_events(self, company: str, limit: int = 10) -> FdaEvents:
        clean = company.strip()
        capped = max(1, min(limit, _MAX_LIMIT))
        approvals, app_status, app_empty = await self._approvals(clean, capped)
        recalls, rec_status, rec_empty = await self._recalls(clean, capped)

        dates = [a.approval_date for a in approvals if a.approval_date]
        dates += [r.report_date for r in recalls if r.report_date]
        as_of = max(dates) if dates else None

        statuses = [s for s in (app_status, rec_status) if s]
        source_status = "; ".join(statuses) if statuses else None

        note = None
        # Only a genuine zero-match when BOTH legs returned (no throttle) and both are empty.
        if app_empty and rec_empty and not statuses:
            note = (
                f"No FDA drug approvals or recalls matched sponsor '{clean}'. The "
                "sponsor-of-record name may differ from the issuer name — try a variant."
            )
        return FdaEvents(
            company=clean,
            approvals=approvals,
            recalls=recalls,
            as_of=as_of,
            source_status=source_status,
            note=note,
        )

    async def _approvals(
        self, name: str, limit: int
    ) -> tuple[list[FdaApproval], str | None, bool]:
        url = _DRUGSFDA_URL.format(name=quote(name), limit=limit)
        try:
            payload = await self._fetch(url)
        except SourceUnavailable as exc:
            return [], f"approvals {exc.status}", False
        except Exception as exc:  # noqa: BLE001 — any non-transient fetch error is honest, not data
            return [], f"approvals {unavailable_status(exc)}", False
        if _is_not_found(payload):
            return [], None, True
        results = (payload or {}).get("results") or []
        approvals: list[FdaApproval] = []
        for result in results:
            if not isinstance(result, dict):
                continue
            application_number = result.get("application_number")
            brand_names = sorted(
                {
                    str(product.get("brand_name")).strip()
                    for product in (result.get("products") or [])
                    if isinstance(product, dict) and product.get("brand_name")
                }
            )
            for submission in result.get("submissions") or []:
                if not isinstance(submission, dict):
                    continue
                if submission.get("submission_status") != _APPROVED:
                    continue
                approvals.append(
                    FdaApproval(
                        approval_date=_parse_fda_date(submission.get("submission_status_date")),
                        application_number=application_number,
                        brand_names=brand_names,
                    )
                )
        approvals.sort(
            key=lambda a: (a.approval_date is not None, a.approval_date), reverse=True
        )
        return approvals[:limit], None, not approvals

    async def _recalls(self, name: str, limit: int) -> tuple[list[FdaRecall], str | None, bool]:
        url = _ENFORCEMENT_URL.format(name=quote(name), limit=limit)
        try:
            payload = await self._fetch(url)
        except SourceUnavailable as exc:
            return [], f"recalls {exc.status}", False
        except Exception as exc:  # noqa: BLE001
            return [], f"recalls {unavailable_status(exc)}", False
        if _is_not_found(payload):
            return [], None, True
        results = (payload or {}).get("results") or []
        recalls: list[FdaRecall] = []
        for result in results:
            if not isinstance(result, dict):
                continue
            recalls.append(
                FdaRecall(
                    report_date=_parse_fda_date(result.get("report_date")),
                    product=result.get("product_description"),
                    reason=result.get("reason_for_recall"),
                    classification=result.get("classification"),
                    status=result.get("status"),
                )
            )
        return recalls[:limit], None, not recalls
