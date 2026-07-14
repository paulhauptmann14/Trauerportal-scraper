import json
from pathlib import Path

import pytest

from pnp_watcher.pnp_client import get_notice_edition, iter_recent_editions

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text())


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    """Returns queued responses in order, recording the requests made."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    def post(self, url, json=None, timeout=None):
        self.requests.append({"url": url, "json": json})
        return self._responses.pop(0)


def test_get_notice_edition_posts_edition_id_and_date():
    payload = load_fixture("notice_edition_regen.json")
    session = FakeSession([FakeResponse(payload)])

    result = get_notice_edition(edition_id=8, date="2026-07-14", session=session)

    assert result == payload
    assert session.requests[0]["json"] == {"editionId": 8, "date": "2026-07-14"}


def test_get_notice_edition_raises_on_http_error():
    session = FakeSession([FakeResponse({}, status_code=500)])

    with pytest.raises(RuntimeError):
        get_notice_edition(edition_id=8, date="2026-07-14", session=session)


def test_iter_recent_editions_follows_prev_chain():
    first = load_fixture("notice_edition_regen.json")
    second = load_fixture("notice_edition_regen_prev.json")
    session = FakeSession([FakeResponse(first), FakeResponse(second)])

    results = list(
        iter_recent_editions(
            edition_id=8, start_date="2026-07-14", max_lookback_days=14, session=session
        )
    )

    assert [r["date"] for r in results] == ["2026-07-14", "2026-07-11"]
    assert session.requests[0]["json"] == {"editionId": 8, "date": "2026-07-14"}
    assert session.requests[1]["json"] == {"editionId": 8, "date": "2026-07-11"}


def test_iter_recent_editions_stops_when_prev_is_null():
    first = load_fixture("notice_edition_regen_prev.json")  # prev is null
    session = FakeSession([FakeResponse(first)])

    results = list(
        iter_recent_editions(
            edition_id=8, start_date="2026-07-11", max_lookback_days=14, session=session
        )
    )

    assert len(results) == 1
    assert len(session.requests) == 1


def test_iter_recent_editions_respects_lookback_limit():
    first = load_fixture("notice_edition_regen.json")
    session = FakeSession([FakeResponse(first)])

    results = list(
        iter_recent_editions(
            edition_id=8, start_date="2026-07-14", max_lookback_days=0, session=session
        )
    )

    assert len(results) == 1
    assert len(session.requests) == 1
