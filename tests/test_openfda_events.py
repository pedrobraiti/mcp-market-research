from datetime import date

from scout.adapters.openfda import OpenFdaEvents


class _Resp:
    def __init__(self, status_code):
        self.status_code = status_code


class _RateLimited(Exception):
    def __init__(self):
        self.response = _Resp(429)
        super().__init__("HTTP 429")


_APPROVALS = {
    "results": [
        {
            "application_number": "NDA021436",
            "products": [
                {"brand_name": "WONDERDRUG"},
                {"brand_name": "WONDERDRUG"},  # duplicate → deduped
            ],
            "submissions": [
                {"submission_status": "AP", "submission_status_date": "20250115"},
                {"submission_status": "TA", "submission_status_date": "20240101"},  # not approved
            ],
        }
    ]
}

_RECALLS = {
    "results": [
        {
            "report_date": "20250320",
            "product_description": "Wonderdrug Tablets 10mg",
            "reason_for_recall": "Cross-contamination",
            "classification": "Class II",
            "status": "Ongoing",
        }
    ]
}

_NOT_FOUND = {"error": {"code": "NOT_FOUND"}}


def _source(fetch):
    return OpenFdaEvents(fetch_json=fetch, retry_attempts=2, retry_base_delay=0.0)


async def test_approvals_and_recalls_parsed():
    async def _fetch(url: str):
        return _APPROVALS if "drugsfda" in url else _RECALLS

    events = await _source(_fetch).get_events("WONDERPHARMA", limit=10)
    assert len(events.approvals) == 1
    approval = events.approvals[0]
    assert approval.approval_date == date(2025, 1, 15)  # the "AP" submission's date
    assert approval.application_number == "NDA021436"
    assert approval.brand_names == ["WONDERDRUG"]  # deduped
    # Serializes under the standard envelope (plain model_dump) as "approval_date".
    assert approval.model_dump(mode="json")["approval_date"] == "2025-01-15"

    assert len(events.recalls) == 1
    recall = events.recalls[0]
    assert recall.report_date == date(2025, 3, 20)
    assert recall.product == "Wonderdrug Tablets 10mg"
    assert recall.reason == "Cross-contamination"
    assert recall.classification == "Class II"
    assert recall.status == "Ongoing"

    assert events.as_of == date(2025, 3, 20)  # newest of the two
    assert events.source_status is None
    assert events.note is None


async def test_zero_matches_404_is_empty_with_note_not_failure():
    async def _fetch(url: str):
        return _NOT_FOUND  # openFDA's zero-match body, served on a 404

    events = await _source(_fetch).get_events("NONESUCH PHARMA", limit=10)
    assert events.approvals == []
    assert events.recalls == []
    assert events.source_status is None  # NOT a fetch failure
    assert events.note is not None and "No FDA drug approvals or recalls" in events.note


async def test_rate_limited_surfaces_source_status():
    async def _fetch(url: str):
        raise _RateLimited()

    events = await _source(_fetch).get_events("WONDERPHARMA", limit=10)
    assert events.approvals == []
    assert events.recalls == []
    assert events.source_status is not None
    assert "approvals unavailable" in events.source_status
    assert "recalls unavailable" in events.source_status
    assert "rate_limited" in events.source_status
    assert events.note is None  # distinct from the zero-match path
