#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
INSTALL_HOME="${HOME}/.local/share/nemo-todo"
BIN_DIR="${HOME}/.local/bin"
SERVICE_DIR="${HOME}/.local/share/kio/servicemenus"
LAUNCHER="${BIN_DIR}/nemo-todo-dolphin"

mkdir -p "${INSTALL_HOME}/core" "${INSTALL_HOME}/platforms" "${INSTALL_HOME}/frontend" "${BIN_DIR}" "${SERVICE_DIR}"
rm -rf "${INSTALL_HOME}/core/nemo_todo_core" "${INSTALL_HOME}/platforms/linux/dolphin" "${INSTALL_HOME}/platforms/linux/nemo" "${INSTALL_HOME}/platforms/linux/common" "${INSTALL_HOME}/frontend"
cp -r "${REPO_ROOT}/core/." "${INSTALL_HOME}/core/"
mkdir -p "${INSTALL_HOME}/platforms/linux"
cp -r "${REPO_ROOT}/platforms/linux/." "${INSTALL_HOME}/platforms/linux/"
cp -r "${REPO_ROOT}/frontend" "${INSTALL_HOME}/frontend"

ln -sfn "${INSTALL_HOME}/platforms/linux/dolphin/launcher.py" "${LAUNCHER}"
sed "s|@LAUNCHER@|${LAUNCHER}|g" \
    "${REPO_ROOT}/platforms/linux/dolphin/nemo-todo.desktop.in" \
    > "${SERVICE_DIR}/nemo-todo.desktop"

chmod +x "${INSTALL_HOME}/platforms/linux/dolphin/launcher.py"
chmod +x "${SERVICE_DIR}/nemo-todo.desktop"

if ! python3 -c "import Xlib" >/dev/null 2>&1; then
    echo "Note: python3-xlib is not installed; the panel will open without snapping next to the Dolphin window."
    echo "Install it (e.g. 'sudo apt install python3-xlib') to enable that docking hack."
fi

echo "Installed the Dolphin TODO service menu. Restart Dolphin if it is already running."