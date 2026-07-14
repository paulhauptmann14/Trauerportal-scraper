import logging
import os
import stat
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger("pnp_watcher")

REGEN_EDITION_ID = 8


def check_env_permissions(path: str) -> str | None:
    """Return a warning if the .env file (which holds the Telegram token) is
    readable/writable by anyone other than the owner, else None."""
    if not path or not os.path.exists(path):
        return None

    mode = stat.S_IMODE(os.stat(path).st_mode)
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        return (
            f"{path} is readable by group/others (mode {oct(mode)}) but contains "
            f"the Telegram bot token. Recommended: chmod 600 {path}"
        )
    return None


@dataclass
class Config:
    target_city: str
    edition_id: int
    lookback_days: int
    telegram_bot_token: str
    telegram_chat_id: str
    state_path: str

    @classmethod
    def load(cls) -> "Config":
        dotenv_path = find_dotenv(usecwd=True)
        load_dotenv(dotenv_path)

        warning = check_env_permissions(dotenv_path)
        if warning:
            logger.warning(warning)

        target_city = os.environ.get("TARGET_CITY", "").strip()
        if not target_city or target_city == "YOUR_TOWN":
            raise ValueError(
                "TARGET_CITY is not set. Please enter a real town name in the "
                ".env file (see .env.example)."
            )

        return cls(
            target_city=target_city,
            edition_id=int(os.environ.get("EDITION_ID", REGEN_EDITION_ID)),
            lookback_days=int(os.environ.get("LOOKBACK_DAYS", 14)),
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            state_path=os.environ.get("STATE_PATH", "state.json"),
        )
