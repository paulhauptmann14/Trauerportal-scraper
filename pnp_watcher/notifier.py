import smtplib
from email.message import EmailMessage

import requests

NOTICE_URL_TEMPLATE = "https://trauer.pnp.de/traueranzeige/{id}"
TELEGRAM_API_BASE = "https://api.telegram.org"


def format_digest(notices: list[dict]) -> str:
    """Deliberately data-minimal: just one link per notice, no names, no
    town, no date. Details stay on trauer.pnp.de instead of landing in the
    notification channel."""
    return "\n".join(NOTICE_URL_TEMPLATE.format(id=notice.get("id")) for notice in notices)


def build_message(target_city: str, notices: list[dict]) -> str:
    header = f"Es ist eine neue Traueranzeige für {target_city} erschienen:"
    return f"{header}\n\n{format_digest(notices)}"


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, target_city: str, session=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.target_city = target_city
        self._session = session or requests.Session()

    def send(self, notices: list[dict]) -> None:
        if not notices:
            return

        response = self._session.post(
            f"{TELEGRAM_API_BASE}/bot{self.bot_token}/sendMessage",
            json={"chat_id": self.chat_id, "text": build_message(self.target_city, notices)},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")


class EmailNotifier:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        recipient: str,
        target_city: str,
        smtp_client_factory=None,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.recipient = recipient
        self.target_city = target_city
        self._smtp_client_factory = smtp_client_factory or smtplib.SMTP

    def send(self, notices: list[dict]) -> None:
        if not notices:
            return

        message = EmailMessage()
        message["Subject"] = f"PNP Trauerportal: {len(notices)} neue Anzeige(n)"
        message["From"] = self.user
        message["To"] = self.recipient
        message.set_content(build_message(self.target_city, notices))

        with self._smtp_client_factory(self.host, self.port) as smtp:
            smtp.starttls()
            smtp.login(self.user, self.password)
            smtp.send_message(message)
