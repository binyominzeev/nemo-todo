#!/usr/bin/env python3
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.nemo_todo_core.database import Database
from core.nemo_todo_core.path_utils import normalize_folder_path
from core.nemo_todo_core.table_service import TableService
from core.nemo_todo_core.todo_service import TodoService

logger = logging.getLogger(__name__)

try:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    from platforms.linux.nemo.panel import TodoPanel
    from platforms.linux.nemo.web_panel import WebKit2, WebTodoPanel
except Exception:  # pragma: no cover
    Gtk = None
    TodoPanel = None
    WebKit2 = None
    WebTodoPanel = None


def run(folder_value: str) -> int:
    if not folder_value:
        print("A folder path is required.", file=sys.stderr)
        return 2

    try:
        folder = normalize_folder_path(folder_value)
    except ValueError as error:
        print(f"Invalid folder: {error}", file=sys.stderr)
        return 2

    if Gtk is None:
        print("GTK 3 and PyGObject are required.", file=sys.stderr)
        return 1

    database = Database()
    database.initialize()
    todo_service = TodoService(database)
    table_service = TableService(database)
    panel_class = WebTodoPanel if WebKit2 is not None else TodoPanel

    try:
        panel = panel_class(todo_service, table_service)
    except Exception:
        if panel_class is TodoPanel:
            raise
        logger.exception("Unable to start WebKit TODO panel; using GTK fallback")
        panel = TodoPanel(todo_service, table_service)

    window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    window.set_title("Nemo TODO")
    window.set_default_size(panel.DEFAULT_WIDTH, 700)
    window.add(panel.widget())
    panel.set_window(window)
    panel.set_folder(folder)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} FOLDER", file=sys.stderr)
        return 2
    return run(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
