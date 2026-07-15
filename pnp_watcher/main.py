import argparse
import logging
import sys
from datetime import date as date_cls
from pathlib import Path

from .config import Config
from .matcher import matches
from .notifier import CompositeNotifier, EmailNotifier, TelegramNotifier, format_digest
from .pnp_client import iter_recent_editions
from .state import State

logger = logging.getLogger("pnp_watcher")


class DryRunNotifier:
    def send(self, notices: list[dict]) -> None:
        if not notices:
            return
        logger.info(
            "[DRY RUN] %d match(es), would send this message:\n%s",
            len(notices),
            format_digest(notices),
        )


def run(config: Config, notifier, fetch_editions=None, today: str | None = None) -> list[dict]:
    today = today or date_cls.today().isoformat()
    if fetch_editions is None:
        def fetch_editions():
            return iter_recent_editions(config.edition_id, today, config.lookback_days)

    state = State.load(config.state_path)
    is_first_run = state.is_first_run
    new_matches = []

    for edition in fetch_editions():
        if not edition.get("success", True):
            logger.warning("Skipping edition response without success=True: %s", edition)
            continue
        for notice in edition.get("notices", []):
            notice_id = notice["id"]
            if state.is_new(notice_id):
                if not is_first_run and matches(notice, config.target_city):
                    new_matches.append(notice)
                state.mark_seen(notice_id)

    if is_first_run:
        logger.info("First run: baseline saved, no notification sent.")

    if new_matches:
        # Sent before saving state: if this raises, state.save() is skipped
        # below, so nothing is persisted and the next run retries everything.
        notifier.send(new_matches)
        logger.info("Reported %d new notice(s) for '%s'.", len(new_matches), config.target_city)

    state.save()
    return new_matches


def _build_email_notifier(config: Config) -> EmailNotifier:
    if not config.smtp_user or not config.smtp_password or not config.notify_email_to:
        raise ValueError(
            "SMTP_USER, SMTP_PASSWORD and NOTIFY_EMAIL_TO must be set in .env "
            "for NOTIFICATION_CHANNEL=email (or use --dry-run to test without sending)."
        )
    return EmailNotifier(
        host=config.smtp_host,
        port=config.smtp_port,
        user=config.smtp_user,
        password=config.smtp_password,
        recipient=config.notify_email_to,
        target_city=config.target_city,
    )


def _build_telegram_notifier(config: Config) -> TelegramNotifier:
    if not config.telegram_bot_token or not config.telegram_chat_id:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env "
            "for NOTIFICATION_CHANNEL=telegram (or use --dry-run to test without Telegram)."
        )
    return TelegramNotifier(
        bot_token=config.telegram_bot_token,
        chat_id=config.telegram_chat_id,
        target_city=config.target_city,
    )


_CHANNEL_BUILDERS = {
    "email": _build_email_notifier,
    "telegram": _build_telegram_notifier,
}


def build_notifier(config: Config):
    """Build the real (non-dry-run) notifier for config.notification_channels.
    A single channel returns that channel's notifier directly; multiple
    channels are combined via CompositeNotifier so all of them get sent to.
    Raises ValueError if the required credentials for any channel are missing."""
    notifiers = [_CHANNEL_BUILDERS[channel](config) for channel in config.notification_channels]
    if len(notifiers) == 1:
        return notifiers[0]
    return CompositeNotifier(notifiers)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PNP Trauerportal Watcher (Landkreis Regen)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the check but skip the real send (log output only).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the stored notice IDs before running (forces a clean restart).",
    )
    return parser


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_arg_parser().parse_args(argv)

    try:
        config = Config.load()
    except ValueError as exc:
        logger.error(str(exc))
        return 1

    if args.reset:
        Path(config.state_path).unlink(missing_ok=True)
        logger.info("State reset (%s deleted).", config.state_path)

    if args.dry_run:
        notifier = DryRunNotifier()
    else:
        try:
            notifier = build_notifier(config)
        except ValueError as exc:
            logger.error(str(exc))
            return 1

    try:
        new_matches = run(config, notifier)
    except Exception as exc:  # noqa: BLE001 - top-level guard, logs and exits non-zero
        logger.error("Run aborted: %s", exc)
        return 1

    if not new_matches:
        logger.info("No new matches for '%s'.", config.target_city)

    return 0


if __name__ == "__main__":
    sys.exit(main())
