#!/usr/bin/env bash
# Tally — one-step setup & run (macOS / Linux)
# Double-click this file on a Mac, or run  ./start.command  in a terminal.

cd "$(dirname "$0")" || exit 1

echo ""
echo "  Tally — starting up"
echo "  ==================="
echo ""

# 1. Find Python
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "  ✗ Python isn't installed."
  echo "    Install it from https://www.python.org/downloads/ then run this again."
  echo ""
  read -p "  Press Return to close." _
  exit 1
fi
echo "  ✓ Found Python: $($PY --version)"

# 2. Create a local virtual environment (keeps your system clean)
if [ ! -d ".venv" ]; then
  echo "  • Setting up a private environment (first run only)…"
  $PY -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# 3. Install dependencies
echo "  • Installing dependencies (first run may take a minute)…"
pip install --quiet --upgrade pip >/dev/null 2>&1
pip install --quiet -r requirements.txt

# 4. Make sure the API key exists
if [ ! -f ".env" ] || ! grep -q "sk-ant" .env 2>/dev/null; then
  echo ""
  echo "  ────────────────────────────────────────────────"
  echo "  One thing needed: your Anthropic API key."
  echo "  Get it at  https://console.anthropic.com  →  API keys"
  echo "  ────────────────────────────────────────────────"
  echo ""
  read -p "  Paste your key here and press Return: " KEY
  echo "ANTHROPIC_API_KEY=${KEY}" > .env
  echo "  ✓ Saved. (You won't be asked again.)"
fi

# 5. Run
echo ""
echo "  ✓ Ready. Opening http://localhost:5000 …"
echo "    (Leave this window open while you use Tally. Close it to stop.)"
echo ""

# Open the browser shortly after the server starts
( sleep 2; (command -v open >/dev/null && open http://localhost:5000) || (command -v xdg-open >/dev/null && xdg-open http://localhost:5000) ) >/dev/null 2>&1 &

$PY app.py
