#!/usr/bin/env bash
# One-shot setup for local dev or a fresh server (Mac or Linux/VPS).
# Safe to re-run: skips steps that are already done.
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creating virtualenv (.venv)..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements-dev.txt -q

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit it before running the watcher."
fi

echo
echo "Setup complete."
echo "  1. Edit .env (TARGET_CITY + NOTIFICATION_CHANNEL credentials)"
echo "  2. source .venv/bin/activate"
echo "  3. python -m pnp_watcher.main --dry-run"
