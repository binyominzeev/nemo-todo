# nemo-todo

`nemo-todo` is a local-only Nemo file manager extension for Linux Mint that adds a lightweight right-side TODO/checklist panel bound to the current folder.

## Features

- Right-side folder-aware panel for TODOs and checklist tables
- Per-folder context using the current Nemo location
- Fast inline TODO create/edit/toggle/delete
- Checklist tables with rows, columns, and boolean cells
- SQLite persistence at `~/.local/share/nemo-todo/todo.db`
- Nemo context menu actions: **Add TODO** and **Toggle TODO Panel**
- Keyboard toggle in panel: `Ctrl+Alt+T`

## Environment

- Linux Mint + Nemo
- Python 3
- GTK 3 (`python3-gi`)
- Nemo Python bindings (`python3-nemo`)

## Install

```bash
./install.sh
nemo -q
```

This installs extension files in:

- `~/.local/share/nemo-python/extensions/nemo_todo.py`
- `~/.local/share/nemo-todo/src/`

## Uninstall

```bash
./uninstall.sh
nemo -q
```

Uninstall keeps your database by default.

## Usage

1. Open Nemo and browse to any folder.
2. Open/toggle panel via Nemo context menu (**Toggle TODO Panel**).
3. Add TODO quickly with `+ New TODO` and press Enter.
4. Edit TODO text inline; toggle completion via checkbox.
5. Add checklist tables with `+ New table`.
6. Add rows/columns inside each table; toggle cells by clicking checkboxes.

Folder changes in Nemo refresh panel data to the exact new folder.

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
