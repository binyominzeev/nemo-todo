#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_HOME="${HOME}/.local/share/nemo-todo"
EXT_DIR="${HOME}/.local/share/nemo-python/extensions"
CORE_DIR="${INSTALL_HOME}/core"
PLATFORM_DIR="${INSTALL_HOME}/platforms"
WEB_DIR="${INSTALL_HOME}/web"
GSETTINGS_DIR="${HOME}/.local/share/glib-2.0/schemas"

mkdir -p "${CORE_DIR}" "${PLATFORM_DIR}" "${EXT_DIR}" "${GSETTINGS_DIR}" "${HOME}/.local/share/nemo-todo"
rm -rf "${CORE_DIR}" "${PLATFORM_DIR}" "${WEB_DIR}"
mkdir -p "${CORE_DIR}" "${PLATFORM_DIR}"
cp -r "${REPO_ROOT}/core/." "${CORE_DIR}/"
cp -r "${REPO_ROOT}/platforms/." "${PLATFORM_DIR}/"
cp -r "${REPO_ROOT}/frontend" "${WEB_DIR}"
rm -rf "${PLATFORM_DIR}/macos" "${PLATFORM_DIR}/windows" "${PLATFORM_DIR}/linux/dolphin"
cp "${REPO_ROOT}/platforms/linux/nemo/org.nemo.extensions.nemo-todo.gschema.xml" "${GSETTINGS_DIR}/"
chmod +x "${PLATFORM_DIR}/linux/nemo/nemo-todo-prefs"
glib-compile-schemas "${GSETTINGS_DIR}"

cat > "${EXT_DIR}/nemo_todo.py" <<PY
import os
import sys

install_home = os.path.expanduser("${INSTALL_HOME}")
if install_home not in sys.path:
    sys.path.insert(0, install_home)

from platforms.linux.nemo.nemo_todo_extension import *  # noqa: F401,F403
PY

echo "Installed nemo-todo extension files."
echo "Restart Nemo to load changes: nemo -q"
