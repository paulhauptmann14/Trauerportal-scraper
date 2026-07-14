import logging
import os
import stat
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger("pnp_watcher")

REGEN_EDITION_ID = 8
VALID_NOTIFICATION_CHANNELS = {"telegram", "email"}


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
    notification_channel: str
    telegram_bot_token: str
    telegram_chat_id: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    notify_email_to: str
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

        notification_channel = os.environ.get("NOTIFICATION_CHANNEL", "telegram").strip().lower()
        if notification_channel not in VALID_NOTIFICATION_CHANNELS:
            raise ValueError(
                f"NOTIFICATION_CHANNEL must be one of {sorted(VALID_NOTIFICATION_CHANNELS)}, "
                f"got '{notification_channel}'."
            )

        return cls(
            target_city=target_city,
            edition_id=int(os.environ.get("EDITION_ID", REGEN_EDITION_ID)),
            lookback_days=int(os.environ.get("LOOKBACK_DAYS", 14)),
            notification_channel=notification_channel,
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            smtp_host=os.environ.get("SMTP_HOST", "smtp.mail.me.com"),
            smtp_port=int(os.environ.get("SMTP_PORT", 587)),
            smtp_user=os.environ.get("SMTP_USER", ""),
            smtp_password=os.environ.get("SMTP_PASSWORD", ""),
            notify_email_to=os.environ.get("NOTIFY_EMAIL_TO", ""),
            state_path=os.environ.get("STATE_PATH", "state.json"),
        )
