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
from platforms.linux.common.dock_config import dock_hack_enabled
from platforms.linux.common.panel_state import load_panel_width, save_panel_width
from platforms.linux.dolphin import x11_dock

logger = logging.getLogger(__name__)

DOCK_CONFIG_PATH = Path.home() / ".config" / "nemo-todo" / "dolphin.json"
PANEL_STATE_PATH = Path.home() / ".config" / "nemo-todo" / "dolphin_panel_width.json"

try:
    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gdk, Gtk
    from platforms.linux.nemo.panel import TodoPanel
    from platforms.linux.nemo.web_panel import WebKit2, WebTodoPanel
except Exception:  # pragma: no cover
    Gdk = None
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
    initial_width = load_panel_width(PANEL_STATE_PATH, panel.DEFAULT_WIDTH)
    window.set_default_size(initial_width, 700)
    window.add(panel.widget())
    panel.set_window(window)
    panel.set_folder(folder)
    window.connect("destroy", Gtk.main_quit)
    window.connect("configure-event", _make_width_persister(initial_width))
    tracker = _setup_dock_hack(window, initial_width)
    window.show_all()
    Gtk.main()
    if tracker is not None:
        tracker.stop()
    return 0


def _make_width_persister(initial_width: int):
    last_width = {"value": initial_width}

    def _on_configure(widget, _event):
        width, _height = widget.get_size()
        if width != last_width["value"]:
            last_width["value"] = width
            save_panel_width(PANEL_STATE_PATH, width)
        return False

    return _on_configure


def _setup_dock_hack(window, panel_width: int):
    """Best-effort: snap the panel beside the active Dolphin window on X11/XWayland."""
    if not dock_hack_enabled(DOCK_CONFIG_PATH):
        return None

    display = x11_dock.open_display()
    if display is None:
        return None

    dolphin_window = x11_dock.find_active_dolphin_window(display)
    if dolphin_window is None:
        display.close()
        return None

    tracker = x11_dock.DockTracker(display, dolphin_window, window, panel_width, on_closed=Gtk.main_quit)
    window.set_gravity(Gdk.Gravity.STATIC)
    window.connect("realize", lambda _widget: tracker.reposition())
    tracker.start()
    return tracker


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} FOLDER", file=sys.stderr)
        return 2
    return run(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
