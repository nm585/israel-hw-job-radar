#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; fi
echo
echo "Setup complete. Edit .env for Telegram, then run:"
echo "  source .venv/bin/activate"
echo "  python run.py --dry-run --no-seed -v"
