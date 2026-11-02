#!/usr/bin/env bash
# =============================================================
#  run.sh — Launcher for the Termux / Linux Media Server
#
#  Place the media-server/ folder anywhere inside a sharing
#  folder.  The server will automatically serve the PARENT
#  directory of media-server/.
#
#  Layout:
#      /some/folder/          ← MEDIA_ROOT (auto-detected)
#          media-server/      ← this app lives here
#              run.sh         ← this script
#          Movie.mkv
#          TV Show/
#
#  Usage:
#      ./run.sh               # start on default port 8080
#      ./run.sh --port 9090   # custom port
#      ./run.sh --help        # show all options
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- Ensure Flask is installed --------------------------------
python3 -c "import flask" 2>/dev/null || {
    echo "Flask not found — installing..."
    pip3 install --quiet flask --break-system-packages \
        || pip3 install --quiet flask --user \
        || { echo "ERROR: Could not install Flask. Run: pip3 install flask"; exit 1; }
    echo "Flask installed."
}

# ---- Start server --------------------------------------------
cd "$SCRIPT_DIR"

# Never write __pycache__ or .pyc files into the app folder
export PYTHONDONTWRITEBYTECODE=1

exec python3 app.py "$@"
