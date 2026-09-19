#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
INSTALL_HOME="${HOME}/.local/share/nemo-todo"
BIN_DIR="${HOME}/.local/bin"
SERVICE_DIR="${HOME}/.local/share/kio/servicemenus"
LAUNCHER="${BIN_DIR}/nemo-todo-dolphin"

mkdir -p "${INSTALL_HOME}/core" "${INSTALL_HOME}/platforms" "${INSTALL_HOME}/frontend" "${BIN_DIR}" "${SERVICE_DIR}"
rm -rf "${INSTALL_HOME}/core/nemo_todo_core" "${INSTALL_HOME}/platforms/linux/dolphin" "${INSTALL_HOME}/platforms/linux/nemo" "${INSTALL_HOME}/frontend"
cp -r "${REPO_ROOT}/core/." "${INSTALL_HOME}/core/"
mkdir -p "${INSTALL_HOME}/platforms/linux"
cp -r "${REPO_ROOT}/platforms/linux/." "${INSTALL_HOME}/platforms/linux/"
cp -r "${REPO_ROOT}/frontend" "${INSTALL_HOME}/frontend"

ln -sfn "${INSTALL_HOME}/platforms/linux/dolphin/launcher.py" "${LAUNCHER}"
sed "s|@LAUNCHER@|${LAUNCHER}|g" \
    "${REPO_ROOT}/platforms/linux/dolphin/nemo-todo.desktop.in" \
    > "${SERVICE_DIR}/nemo-todo.desktop"

chmod +x "${INSTALL_HOME}/platforms/linux/dolphin/launcher.py"
echo "Installed the Dolphin TODO service menu. Restart Dolphin if it is already running."