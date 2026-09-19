# nemo-todo

`nemo-todo` is a local-only, folder-aware TODO and checklist application with file-manager integrations. The Nemo integration is supported, and the first Dolphin port is available as a KDE service-menu action that opens a separate floating panel for the current folder.

<img width="1794" height="740" alt="Screenshot from 2026-09-18 15-02-02" src="https://github.com/user-attachments/assets/1c636ba2-5a9e-4ab7-a4f0-0715369db67b" />


## Status

- **Linux / Nemo:** supported
- **Linux / Dolphin:** first port implemented; opens a separate floating GTK window from the folder background menu
- **macOS / Finder:** placeholder only
- **Windows / File Explorer:** placeholder only

The Dolphin version is intentionally not a docked Dolphin sidebar. A docked panel would require a separate, deeper Dolphin/KDE plugin project.

## Features

- Folder-aware floating TODO/checklist window
- Per-folder context using the current Nemo location
- Fast inline TODO create/edit/toggle/delete
- Checklist tables with rows, columns, and boolean cells
- Scrollable checklist workspace with table and card views
- SQLite persistence at `~/.local/share/nemo-todo/todo.db`
- Nemo context menu action: **Toggle TODO Panel**
- Configurable Nemo keyboard shortcut for toggling the panel
- Dolphin folder background action: **Open TODO panel here**

## Architecture

```text
core/nemo_todo_core/       Shared database, models, services and bridge
frontend/                  Shared HTML/CSS/JavaScript frontend
platforms/linux/nemo/      Nemo, GTK 3 and WebKitGTK adapter
platforms/linux/dolphin/  Dolphin launcher and KDE service menu
platforms/macos/           Finder Sync implementation placeholder
platforms/windows/         File Explorer implementation placeholder
tests/                     Core and platform-specific tests
```

The core is UI-independent. The frontend communicates with it through the bridge; it does not access SQLite directly. Platform adapters provide the current folder and create the native window or WebView host.

## Linux / Nemo

- Linux Mint + Nemo
- Python 3
- GTK 3 (`python3-gi`)
- WebKitGTK 4.0 (`gir1.2-webkit2-4.0`, `python3-gi`)
- XApp GTK bindings (`gir1.2-xapp-1.0`)
- Nemo Python bindings (`python3-nemo`)

## Install

```bash
./install.sh
nemo -q
```

This installs the Nemo extension and its runtime files in:

- `~/.local/share/nemo-python/extensions/nemo_todo.py`
- `~/.local/share/nemo-todo/core/`
- `~/.local/share/nemo-todo/platforms/linux/nemo/`
- `~/.local/share/nemo-todo/web/`
- `~/.local/share/glib-2.0/schemas/org.nemo.extensions.nemo-todo.gschema.xml`

## Uninstall

```bash
./uninstall.sh
nemo -q
```

Uninstall keeps your database by default.

## Linux / Dolphin

The Dolphin port uses a KDE service menu and a separate GTK window. It does not modify the Dolphin layout.

Requirements:

- Python 3
- GTK 3 (`python3-gi`)
- WebKitGTK 4.0 for the web UI, with a GTK fallback
- Dolphin/KDE service-menu support

Install it with:

```bash
./platforms/linux/dolphin/install.sh
```

Then right-click the background of a Dolphin folder and select **Open TODO panel here**. Uninstall with:

```bash
./platforms/linux/dolphin/uninstall.sh
```

The Dolphin launcher accepts a local path or `file://` URI and uses the same SQLite database and folder-aware services as the Nemo integration.

## Usage

1. Open Nemo and browse to any folder.
2. Use the context menu (**Toggle TODO Panel**) to show or hide the separate TODO window.
3. Open **Edit > Plugins > Extensions**, select **Nemo TODO**, and click **Configure**.
4. Set the keyboard shortcut in the preferences panel; it works while the Nemo window has focus. The default is `Ctrl+Alt+T`.
5. Use the panel's **New TODO** or **New table** command to add an item for the current folder.
6. Edit TODO text inline; toggle completion via checkbox.
7. Switch all checklist tables between the compact table view and the card view.
8. Rename or delete a checklist table inline.
9. Add, rename, or delete rows and columns inside each table; toggle cells by clicking checkboxes.

Folder changes in Nemo refresh panel data to the exact new folder. Dolphin starts the panel for the folder passed by its service menu.

The panel uses a local WebKitGTK frontend for its flexible layout and falls back
to the GTK implementation if WebKitGTK is unavailable. The frontend never
accesses SQLite directly; commands go through the Python service bridge.

## Other platforms

### macOS / Finder

`platforms/macos/README.md` describes the planned Finder Sync Extension plus a separate SwiftUI/AppKit application. There is no macOS implementation in this repository yet, and Finder-docked panels are not part of the planned first version.

### Windows / File Explorer

`platforms/windows/README.md` describes the planned static Explorer shell verb, followed by `IExplorerCommand` if needed, plus a WinUI 3/WPF application. There is no Windows implementation in this repository yet, and Explorer-docked panels are not part of the planned first version.

## Development

Run tests:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Nemo reload during development

```bash
nemo -q
nemo &
```
