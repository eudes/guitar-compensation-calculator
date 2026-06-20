#!/usr/bin/env bash
# Serve the calculator over http:// and open it in your browser.
#
# Why this is needed: the 3D preview uses ES-module imports, an import map, and
# fetches the OpenSCAD WebAssembly engine. Browsers block all of that under the
# file:// origin, so opening index.html directly shows no preview. Serving over
# http:// (what this script does) makes it work.
#
# Usage:  ./serve.sh [port]      (default port 8136)

set -euo pipefail

PORT="${1:-8136}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL="http://localhost:${PORT}/index.html"

# Pick a Python.
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python  >/dev/null 2>&1; then PY=python
else echo "Need Python (python3) to run the local server." >&2; exit 1
fi

# If the port is already taken, just open the page (assume a server is up).
if lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port ${PORT} already in use — opening ${URL}"
else
  echo "Serving ${DIR} at ${URL}"
  "${PY}" -m http.server "${PORT}" --directory "${DIR}" >/dev/null 2>&1 &
  SERVER_PID=$!
  trap 'kill "${SERVER_PID}" 2>/dev/null || true' EXIT INT TERM
  # Wait for the server to accept connections.
  for _ in $(seq 1 50); do
    if lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then break; fi
    sleep 0.1
  done
fi

# Open in the default browser (macOS: open, Linux: xdg-open, Windows/Git-Bash: start).
if   command -v open      >/dev/null 2>&1; then open "${URL}"
elif command -v xdg-open  >/dev/null 2>&1; then xdg-open "${URL}"
elif command -v start     >/dev/null 2>&1; then start "" "${URL}"
else echo "Open this in your browser: ${URL}"
fi

# Keep the script (and the server) alive until Ctrl-C, unless we reused an existing one.
if [ -n "${SERVER_PID:-}" ]; then
  echo "Press Ctrl-C to stop the server."
  wait "${SERVER_PID}"
fi
