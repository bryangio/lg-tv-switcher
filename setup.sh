#!/bin/bash
set -e

echo "=== LG TV Switcher Setup ==="
echo ""

# Install websocket-client
echo "Installing websocket-client..."
pip3 install --user websocket-client
echo ""

# Run first-time pairing
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/lg_switch.py" --setup "$@"
