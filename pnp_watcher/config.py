import os
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

REGEN_EDITION_ID = 8
VALID_NOTIFICATION_CHANNELS = {"telegram", "email"}


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
        load_dotenv(find_dotenv(usecwd=True))

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
