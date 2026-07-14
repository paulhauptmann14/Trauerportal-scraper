# PNP Trauerportal Watcher

Watches trauer.pnp.de for new obituaries in Landkreis Regen for a
configured town and sends a notification — via Telegram or email,
your choice — on a match.

## Architecture

```
pnp_watcher/
  config.py       Loads settings from .env (TARGET_CITY, Telegram credentials,
                   lookback window) and warns if .env has insecure file permissions.
  pnp_client.py    Talks to trauer.pnp.de's public JSON API: fetches one day's
                   notices and walks the `prev` chain backwards to catch up
                   on days since the last run.
  matcher.py       Checks whether a notice mentions the configured town
                   (case-insensitive substring match).
  state.py         Tracks which notice IDs have already been seen, persisted
                   in state.json, so nothing is reported twice.
  notifier.py      Sends the notification — TelegramNotifier or
                   EmailNotifier, picked via NOTIFICATION_CHANNEL — just a
                   link per matching notice, no names/towns/dates.
  main.py          CLI entry point (--dry-run, --reset) that wires the above
                   together into a single run.
tests/             Unit tests per module, plus recorded API fixtures under
                   tests/fixtures/ (all fictional data).
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
chmod 600 .env
# Open .env and fill in TARGET_CITY, then set NOTIFICATION_CHANNEL to
# "telegram" or "email" and fill in the matching credentials below it:
# - telegram: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (create a bot via
#   @BotFather, find your chat ID e.g. via
#   https://api.telegram.org/bot<TOKEN>/getUpdates after messaging the bot)
# - email: SMTP_USER, SMTP_PASSWORD, NOTIFY_EMAIL_TO (SMTP_HOST/PORT
#   default to iCloud Mail; use an app-specific password, not your
#   regular account password)
```

## Running

```bash
# Test run without a real send
python -m pnp_watcher.main --dry-run

# Real run
python -m pnp_watcher.main

# Reset state (e.g. to re-test after changing TARGET_CITY)
python -m pnp_watcher.main --reset --dry-run
```

The very first run only saves a baseline (`state.json`) and sends nothing.
From the second run onward, newly appeared notices are reported.

## Tests

```bash
python -m pytest -q
```
