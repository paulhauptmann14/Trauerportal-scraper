from datetime import datetime

import requests

API_BASE = "https://trauer.pnp.de/api/public/v1"


def get_notice_edition(edition_id: int, date: str, session=None, timeout: float = 10) -> dict:
    session = session or requests.Session()
    response = session.post(
        f"{API_BASE}/get-notice-edition",
        json={"editionId": edition_id, "date": date},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def iter_recent_editions(edition_id: int, start_date: str, max_lookback_days: int, session=None):
    """Yield the edition for start_date, then follow the `prev` chain backwards
    until either there is no earlier edition or max_lookback_days is exceeded."""
    session = session or requests.Session()
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    current_date = start_date

    while True:
        result = get_notice_edition(edition_id, current_date, session=session)
        yield result

        prev = result.get("prev")
        if not prev or not prev.get("sterbetag"):
            return

        prev_date_str = prev["sterbetag"]
        prev_date = datetime.strptime(prev_date_str, "%Y-%m-%d").date()
        if (start - prev_date).days > max_lookback_days:
            return

        current_date = prev_date_str
