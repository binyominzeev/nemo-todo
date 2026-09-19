#!/usr/bin/env bash
set -euo pipefail

EXT_FILE="${HOME}/.local/share/nemo-python/extensions/nemo_todo.py"
INSTALL_HOME="${HOME}/.local/share/nemo-todo"
GSETTINGS_DIR="${HOME}/.local/share/glib-2.0/schemas"

rm -f "${EXT_FILE}"
rm -rf "${INSTALL_HOME}/core"
rm -rf "${INSTALL_HOME}/platforms"
rm -rf "${INSTALL_HOME}/web"
rm -f "${GSETTINGS_DIR}/org.nemo.extensions.nemo-todo.gschema.xml"
if command -v glib-compile-schemas >/dev/null 2>&1 && [[ -d "${GSETTINGS_DIR}" ]]; then
	glib-compile-schemas "${GSETTINGS_DIR}"
fi

echo "Removed nemo-todo extension files."
echo "Database preserved at ~/.local/share/nemo-todo/todo.db"
