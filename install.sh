#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_HOME="${HOME}/.local/share/nemo-todo"
EXT_DIR="${HOME}/.local/share/nemo-python/extensions"
SRC_DIR="${INSTALL_HOME}/src"
WEB_DIR="${INSTALL_HOME}/web"

mkdir -p "${SRC_DIR}" "${EXT_DIR}" "${HOME}/.local/share/nemo-todo"
rm -rf "${SRC_DIR}"
rm -rf "${WEB_DIR}"
mkdir -p "${SRC_DIR}"
cp -r "${REPO_ROOT}/src/." "${SRC_DIR}/"
cp -r "${REPO_ROOT}/web" "${WEB_DIR}"

cat > "${EXT_DIR}/nemo_todo.py" <<PY
import os
import sys

install_home = os.path.expanduser("${INSTALL_HOME}")
if install_home not in sys.path:
    sys.path.insert(0, install_home)

from src.nemo_todo_extension import *  # noqa: F401,F403
PY

echo "Installed nemo-todo extension files."
echo "Restart Nemo to load changes: nemo -q"
