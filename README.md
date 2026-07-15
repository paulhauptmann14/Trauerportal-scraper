# PNP Trauerportal Watcher

Watches trauer.pnp.de for new obituaries in Landkreis Regen for a
configured town and sends a notification — via Telegram or email,
your choice — on a match.

## Architecture

```
pnp_watcher/
  config.py       Loads settings from .env (TARGET_CITY, Telegram/email
                   credentials, lookback window).
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
./setup.sh
# or manually:
#   python3 -m venv .venv && source .venv/bin/activate
#   pip install -r requirements-dev.txt
#   cp .env.example .env
```

Then edit `.env`: fill in `TARGET_CITY`, set `NOTIFICATION_CHANNEL` to
`telegram` or `email`, and fill in the matching credentials below it:
- telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (create a bot via
  @BotFather, find your chat ID e.g. via
  `https://api.telegram.org/bot<TOKEN>/getUpdates` after messaging the bot)
- email: `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_EMAIL_TO` (`SMTP_HOST`/`PORT`
  default to iCloud Mail; use an app-specific password, not your regular
  account password)

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

## Deployment (VPS)

Runs on any Linux server with Python 3.10+ — no OS-specific dependencies,
no Docker required for a script this small.

```bash
git clone <this-repo-url>
cd trauerportal-scraper
./setup.sh
# edit .env as described above, then verify:
.venv/bin/python -m pnp_watcher.main --dry-run
```

Schedule it with plain `cron` (`crontab -e`), e.g. every 30 minutes:

```
*/30 * * * * cd /opt/trauerportal-scraper && .venv/bin/python -m pnp_watcher.main >> watcher.log 2>&1
```

If you redirect logs to a file: the log line on a successful match
deliberately only contains a count (`"Reported 1 new notice(s) for
'Kollnburg'"`), no names — same for the notification itself, which only
ever contains a link, not names/towns/dates (see `notifier.py`).

Alternative: a systemd user timer instead of cron gives you `journalctl`
logs and automatic restart-on-failure — worth it once you're actually on
the VPS, not needed for the cron-based setup above.

## Tests

```bash
python -m pytest -q
```
