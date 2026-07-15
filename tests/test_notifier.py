import pytest

from pnp_watcher.notifier import CompositeNotifier, EmailNotifier, TelegramNotifier, format_digest


def make_notice(id=1, vname="Max", nname="Mustermann", wohnort="Fiktingen", sterbetag="2026-07-14"):
    return {
        "id": id,
        "vname": vname,
        "nname": nname,
        "wohnort": wohnort,
        "sterbetag": sterbetag,
    }


def test_format_digest_links_to_each_notice_by_id_only():
    notices = [make_notice(id=1, nname="Mustermann"), make_notice(id=2, nname="Musterfrau")]
    body = format_digest(notices)

    assert "https://trauer.pnp.de/traueranzeige/1" in body
    assert "https://trauer.pnp.de/traueranzeige/2" in body


def test_format_digest_does_not_include_names_or_wohnort():
    notices = [make_notice(id=1, vname="Max", nname="Mustermann", wohnort="Fiktingen/Beispielstadt")]
    body = format_digest(notices)

    assert "Mustermann" not in body
    assert "Max" not in body
    assert "Fiktingen/Beispielstadt" not in body


class FakeTelegramResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeTelegramSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    def post(self, url, json=None, timeout=None):
        self.requests.append({"url": url, "json": json})
        return self._responses.pop(0)


def test_telegram_notifier_sends_digest_to_chat():
    session = FakeTelegramSession([FakeTelegramResponse({"ok": True})])
    notifier = TelegramNotifier(bot_token="123:ABC", chat_id="42", target_city="Fiktingen", session=session)

    notifier.send([make_notice(id=1), make_notice(id=2)])

    assert len(session.requests) == 1
    request = session.requests[0]
    assert request["url"] == "https://api.telegram.org/bot123:ABC/sendMessage"
    assert request["json"]["chat_id"] == "42"
    assert request["json"]["text"].startswith(
        "Es ist eine neue Traueranzeige für Fiktingen erschienen:"
    )
    assert "https://trauer.pnp.de/traueranzeige/1" in request["json"]["text"]
    assert "https://trauer.pnp.de/traueranzeige/2" in request["json"]["text"]


def test_telegram_notifier_sends_nothing_for_empty_list():
    session = FakeTelegramSession([])
    notifier = TelegramNotifier(bot_token="123:ABC", chat_id="42", target_city="Fiktingen", session=session)

    notifier.send([])

    assert session.requests == []


def test_telegram_notifier_raises_when_api_reports_not_ok():
    session = FakeTelegramSession([FakeTelegramResponse({"ok": False, "description": "chat not found"})])
    notifier = TelegramNotifier(bot_token="123:ABC", chat_id="42", target_city="Fiktingen", session=session)

    with pytest.raises(RuntimeError):
        notifier.send([make_notice()])


def test_telegram_notifier_raises_on_http_error():
    session = FakeTelegramSession([FakeTelegramResponse({}, status_code=500)])
    notifier = TelegramNotifier(bot_token="123:ABC", chat_id="42", target_city="Fiktingen", session=session)

    with pytest.raises(RuntimeError):
        notifier.send([make_notice()])


class FakeSMTP:
    def __init__(self):
        self.sent = []
        self.logged_in = None
        self.started_tls = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, user, password):
        self.logged_in = (user, password)

    def send_message(self, message):
        self.sent.append(message)


def make_email_notifier(smtp, **overrides):
    kwargs = dict(
        host="smtp.mail.me.com",
        port=587,
        user="me@icloud.com",
        password="app-password",
        recipient="me@icloud.com",
        target_city="Fiktingen",
        smtp_client_factory=lambda host, port: smtp,
    )
    kwargs.update(overrides)
    return EmailNotifier(**kwargs)


def test_email_notifier_sends_one_message_via_smtp():
    smtp = FakeSMTP()
    notifier = make_email_notifier(smtp)

    notifier.send([make_notice(id=1), make_notice(id=2)])

    assert smtp.logged_in == ("me@icloud.com", "app-password")
    assert smtp.started_tls is True
    assert len(smtp.sent) == 1
    sent = smtp.sent[0]
    assert sent["To"] == "me@icloud.com"
    body = sent.get_content()
    assert body.startswith("Es ist eine neue Traueranzeige für Fiktingen erschienen:")
    assert "https://trauer.pnp.de/traueranzeige/1" in body
    assert "https://trauer.pnp.de/traueranzeige/2" in body
    assert "Mustermann" not in body


def test_email_notifier_sends_nothing_for_empty_list():
    smtp = FakeSMTP()
    notifier = make_email_notifier(smtp)

    notifier.send([])

    assert smtp.sent == []


class RecordingNotifier:
    def __init__(self, fail=False):
        self.fail = fail
        self.sent_batches = []

    def send(self, notices):
        if self.fail:
            raise RuntimeError("boom")
        self.sent_batches.append(notices)


def test_composite_notifier_sends_via_all_notifiers():
    telegram = RecordingNotifier()
    email = RecordingNotifier()
    notifier = CompositeNotifier([telegram, email])

    notices = [make_notice(id=1)]
    notifier.send(notices)

    assert telegram.sent_batches == [notices]
    assert email.sent_batches == [notices]


def test_composite_notifier_propagates_failure_from_any_notifier():
    telegram = RecordingNotifier()
    email = RecordingNotifier(fail=True)
    notifier = CompositeNotifier([telegram, email])

    with pytest.raises(RuntimeError):
        notifier.send([make_notice()])
