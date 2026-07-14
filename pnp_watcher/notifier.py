import requests

NOTICE_URL_TEMPLATE = "https://trauer.pnp.de/traueranzeige/{id}"
TELEGRAM_API_BASE = "https://api.telegram.org"


def format_digest(notices: list[dict]) -> str:
    """Deliberately data-minimal: just one link per notice, no names, no
    town, no date. Details stay on trauer.pnp.de instead of landing in Telegram."""
    return "\n".join(NOTICE_URL_TEMPLATE.format(id=notice.get("id")) for notice in notices)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, target_city: str, session=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.target_city = target_city
        self._session = session or requests.Session()

    def send(self, notices: list[dict]) -> None:
        if not notices:
            return

        header = f"Es ist eine neue Traueranzeige für {self.target_city} erschienen:"
        text = f"{header}\n\n{format_digest(notices)}"

        response = self._session.post(
            f"{TELEGRAM_API_BASE}/bot{self.bot_token}/sendMessage",
            json={"chat_id": self.chat_id, "text": text},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error: {data}")
