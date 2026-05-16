#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Lyrics App Launcher
#  Double-click this file in Finder to start the app.
# ─────────────────────────────────────────────────────────────

# Change to the directory this script lives in
cd "$(dirname "$0")"

APP_PORT=8765
APP_URL="http://localhost:${APP_PORT}"
VENV_DIR=".venv"
PID_FILE=".server.pid"

# ── Helper: print to Terminal window ────────────────────────
log() { echo "[Lyrics] $*"; }

# ── Check if server is already running ──────────────────────
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    log "Server already running (PID $OLD_PID). Opening browser…"
    open "$APP_URL"
    exit 0
  else
    rm -f "$PID_FILE"
  fi
fi

# ── Ensure Python 3 is available ────────────────────────────
if ! command -v python3 &>/dev/null; then
  osascript -e 'display alert "Python 3 not found" message "Please install Python 3 from python.org or via Homebrew (brew install python3)." as critical'
  exit 1
fi

# ── Create virtualenv if needed ─────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
  log "Creating virtual environment…"
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# ── Install/update dependencies ─────────────────────────────
log "Checking dependencies…"
pip install -q -r requirements.txt

# ── Start the server ────────────────────────────────────────
log "Starting server on $APP_URL …"
python3 main.py &
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"

# ── Wait for server to be ready, then open browser ──────────
log "Waiting for server…"
for i in $(seq 1 20); do
  sleep 0.5
  if curl -s "$APP_URL" > /dev/null 2>&1; then
    log "Server ready. Opening browser…"
    open "$APP_URL"
    break
  fi
done

# ── Keep Terminal open so you can see logs / Ctrl-C to stop ─
log "Server is running. Close this window or press Ctrl-C to stop."
wait $SERVER_PID

# Cleanup on exit
rm -f "$PID_FILE"
log "Server stopped."
