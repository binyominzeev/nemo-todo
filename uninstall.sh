#!/usr/bin/env bash
set -euo pipefail

EXT_FILE="${HOME}/.local/share/nemo-python/extensions/nemo_todo.py"
INSTALL_HOME="${HOME}/.local/share/nemo-todo"

rm -f "${EXT_FILE}"
rm -rf "${INSTALL_HOME}/src"
rm -rf "${INSTALL_HOME}/web"

echo "Removed nemo-todo extension files."
echo "Database preserved at ~/.local/share/nemo-todo/todo.db"
