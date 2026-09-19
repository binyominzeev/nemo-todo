#!/usr/bin/env bash
set -euo pipefail

INSTALL_HOME="${HOME}/.local/share/nemo-todo"
rm -f "${HOME}/.local/bin/nemo-todo-dolphin"
rm -f "${HOME}/.local/share/kio/servicemenus/nemo-todo.desktop"
rm -rf "${INSTALL_HOME}/platforms/linux/dolphin"
echo "Removed the Dolphin TODO service menu."