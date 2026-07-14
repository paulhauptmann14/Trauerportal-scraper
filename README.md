# PNP Trauerportal Watcher

Watches trauer.pnp.de for new obituaries in Landkreis Regen for a
configured town and sends a Telegram message on a match.

## Architecture

```
pnp_watcher/
  config.py       Loads settings from .env (TARGET_ORT, Telegram credentials,
                   lookback window) and warns if .env has insecure file permissions.
  pnp_client.py    Talks to trauer.pnp.de's public JSON API: fetches one day's
                   notices and walks the `prev` chain backwards to catch up
                   on days since the last run.
  matcher.py       Checks whether a notice mentions the configured town
                   (case-insensitive substring match).
  state.py         Tracks which notice IDs have already been seen, persisted
                   in state.json, so nothing is reported twice.
  notifier.py      Sends the Telegram message (TelegramNotifier) — just a
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
# Open .env and fill in at least TARGET_ORT, TELEGRAM_BOT_TOKEN and
# TELEGRAM_CHAT_ID (create a bot via @BotFather, find your chat ID e.g.
# via https://api.telegram.org/bot<TOKEN>/getUpdates after messaging
# the bot once)
```

## Running

```bash
# Test run without a real Telegram send
python -m pnp_watcher.main --dry-run

# Real run
python -m pnp_watcher.main

# Reset state (e.g. to re-test after changing TARGET_ORT)
python -m pnp_watcher.main --reset --dry-run
```

The very first run only saves a baseline (`state.json`) and sends nothing.
From the second run onward, newly appeared notices are reported.

## Tests

```bash
python -m pytest -q
```
