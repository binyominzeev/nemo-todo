# nemo-todo

`nemo-todo` is a local-only Nemo file manager extension for Linux Mint that adds a lightweight floating TODO/checklist window bound to the current folder.

<img width="1794" height="740" alt="Screenshot from 2026-09-18 15-02-02" src="https://github.com/user-attachments/assets/1c636ba2-5a9e-4ab7-a4f0-0715369db67b" />


## Features

- Folder-aware floating TODO/checklist window
- Per-folder context using the current Nemo location
- Fast inline TODO create/edit/toggle/delete
- Checklist tables with rows, columns, and boolean cells
- Scrollable checklist workspace with table and card views
- SQLite persistence at `~/.local/share/nemo-todo/todo.db`
- Nemo context menu actions: **Add TODO** and **Toggle TODO Panel**
- Keyboard toggle in panel: `Ctrl+Alt+T`

## Environment

- Linux Mint + Nemo
- Python 3
- GTK 3 (`python3-gi`)
- WebKitGTK 4.0 (`gir1.2-webkit2-4.0`, `python3-gi`)
- Nemo Python bindings (`python3-nemo`)

## Install

```bash
./install.sh
nemo -q
```

This installs extension files in:

- `~/.local/share/nemo-python/extensions/nemo_todo.py`
- `~/.local/share/nemo-todo/src/`
- `~/.local/share/nemo-todo/web/`

## Uninstall

```bash
./uninstall.sh
nemo -q
```

Uninstall keeps your database by default.

## Usage

1. Open Nemo and browse to any folder.
2. Use the context menu (**Toggle TODO Panel**) to show or hide the separate TODO window.
3. Use the top-bar **New TODO** or **New table** command to add an item for the current folder.
4. Edit TODO text inline; toggle completion via checkbox.
5. Switch all checklist tables between the compact table view and the card view.
6. Rename or delete a checklist table inline.
7. Add, rename, or delete rows and columns inside each table; toggle cells by clicking checkboxes.

Folder changes in Nemo refresh panel data to the exact new folder.

The panel uses a local WebKitGTK frontend for its flexible layout and falls back
to the GTK implementation if WebKitGTK is unavailable. The frontend never
accesses SQLite directly; commands go through the Python service bridge.

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
