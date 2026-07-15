import dataclasses

import pytest

from pnp_watcher.config import Config
from pnp_watcher.main import build_notifier, run
from pnp_watcher.notifier import CompositeNotifier, EmailNotifier, TelegramNotifier
from pnp_watcher.state import State


def make_config(tmp_path, target_city="Fiktingen"):
    return Config(
        target_city=target_city,
        edition_id=8,
        lookback_days=14,
        notification_channels=("telegram",),
        telegram_bot_token="123:ABC",
        telegram_chat_id="42",
        smtp_host="smtp.mail.me.com",
        smtp_port=587,
        smtp_user="me@example.com",
        smtp_password="secret",
        notify_email_to="me@example.com",
        state_path=str(tmp_path / "state.json"),
    )


def edition(date, prev, notices):
    return {"success": True, "date": date, "prev": prev, "notices": notices}


def notice(id, wohnort):
    return {
        "id": id,
        "vname": "Max",
        "nname": "Mustermann",
        "wohnort": wohnort,
        "sterbetag": "2026-07-14",
        "weitere_orte": "",
        "notice_text": "",
    }


class RecordingNotifier:
    def __init__(self):
        self.sent_batches = []

    def send(self, notices):
        self.sent_batches.append(notices)


def test_first_run_builds_baseline_without_notifying(tmp_path):
    config = make_config(tmp_path)
    editions = [edition("2026-07-14", None, [notice(1, "Fiktingen")])]
    notifier = RecordingNotifier()

    run(config, notifier=notifier, fetch_editions=lambda: iter(editions), today="2026-07-14")

    assert notifier.sent_batches == []
    state = State.load(tmp_path / "state.json")
    assert state.is_new(1) is False


def test_second_run_notifies_only_new_matching_notices(tmp_path):
    config = make_config(tmp_path)
    notifier = RecordingNotifier()

    first_run_editions = [edition("2026-07-14", None, [notice(1, "Fiktingen")])]
    run(config, notifier=notifier, fetch_editions=lambda: iter(first_run_editions), today="2026-07-14")

    second_run_editions = [
        edition("2026-07-15", None, [notice(1, "Fiktingen"), notice(2, "Fiktingen"), notice(3, "Nebendorf")])
    ]
    run(config, notifier=notifier, fetch_editions=lambda: iter(second_run_editions), today="2026-07-15")

    assert len(notifier.sent_batches) == 1
    sent_ids = [n["id"] for n in notifier.sent_batches[0]]
    assert sent_ids == [2]


def test_run_does_not_notify_when_no_new_matches(tmp_path):
    config = make_config(tmp_path)
    notifier = RecordingNotifier()

    editions = [edition("2026-07-14", None, [notice(1, "Nebendorf")])]
    run(config, notifier=notifier, fetch_editions=lambda: iter(editions), today="2026-07-14")

    assert notifier.sent_batches == []


def test_build_notifier_returns_telegram_notifier_for_telegram_channel(tmp_path):
    config = make_config(tmp_path)
    config = dataclasses.replace(config, notification_channels=("telegram",))

    notifier = build_notifier(config)

    assert isinstance(notifier, TelegramNotifier)


def test_build_notifier_returns_email_notifier_for_email_channel(tmp_path):
    config = make_config(tmp_path)
    config = dataclasses.replace(config, notification_channels=("email",))

    notifier = build_notifier(config)

    assert isinstance(notifier, EmailNotifier)


def test_build_notifier_returns_composite_notifier_for_multiple_channels(tmp_path):
    config = make_config(tmp_path)
    config = dataclasses.replace(config, notification_channels=("telegram", "email"))

    notifier = build_notifier(config)

    assert isinstance(notifier, CompositeNotifier)
    assert len(notifier._notifiers) == 2
    assert isinstance(notifier._notifiers[0], TelegramNotifier)
    assert isinstance(notifier._notifiers[1], EmailNotifier)


def test_build_notifier_raises_when_telegram_credentials_missing(tmp_path):
    config = make_config(tmp_path)
    config = dataclasses.replace(
        config, notification_channels=("telegram",), telegram_bot_token="", telegram_chat_id=""
    )

    with pytest.raises(ValueError):
        build_notifier(config)


def test_build_notifier_raises_when_email_credentials_missing(tmp_path):
    config = make_config(tmp_path)
    config = dataclasses.replace(
        config, notification_channels=("email",), smtp_user="", smtp_password=""
    )

    with pytest.raises(ValueError):
        build_notifier(config)


def test_build_notifier_raises_when_any_channel_in_composite_is_missing_credentials(tmp_path):
    config = make_config(tmp_path)
    config = dataclasses.replace(
        config, notification_channels=("telegram", "email"), smtp_user="", smtp_password=""
    )

    with pytest.raises(ValueError):
        build_notifier(config)
