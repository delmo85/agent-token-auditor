#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)"
if command -v python3 &>/dev/null; then
    python3 "$SCRIPT_DIR/log_iteration_tokens.py"
else
    python "$SCRIPT_DIR/log_iteration_tokens.py"
fi

