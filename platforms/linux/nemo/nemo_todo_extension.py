import logging
import os

from core.nemo_todo_core.database import Database
from .panel import TodoPanel
from core.nemo_todo_core.path_utils import normalize_folder_path
from core.nemo_todo_core.table_service import TableService
from core.nemo_todo_core.todo_service import TodoService
from .web_panel import WebKit2, WebTodoPanel

logger = logging.getLogger(__name__)

try:
    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("Nemo", "3.0")
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gdk, Gio, GObject, Gtk, Nemo
except Exception:  # pragma: no cover
    Gdk = None
    Gio = None
    GObject = None
    Nemo = None


class _WindowState:
    def __init__(self, panel: TodoPanel, todo_window):
        self.panel = panel
        self.todo_window = todo_window


if GObject is not None and Nemo is not None:

    class NemoTodoExtension(
        GObject.GObject, Nemo.MenuProvider, Nemo.LocationWidgetProvider, Nemo.NameAndDescProvider
    ):
        def __init__(self):
            super().__init__()
            self.settings = Gio.Settings.new("org.nemo.extensions.nemo-todo")
            self.database = Database()
            self.database.initialize()
            self.todo_service = TodoService(self.database)
            self.table_service = TableService(self.database)
            self.window_states = {}
            self.key_windows = set()

        def get_name_and_desc(self):
            preferences = os.path.expanduser("~/.local/share/nemo-todo/platforms/linux/nemo/nemo-todo-prefs")
            return [(f"nemo-todo:::Folder-aware TODO and checklist panel:::{preferences}")]

        def get_background_items(self, window, current_folder):
            if current_folder is None:
                return []
            folder_path = None
            try:
                folder_path = normalize_folder_path(current_folder.get_uri())
            except Exception:
                logger.exception("Unable to resolve current folder from Nemo")

            state = self._get_or_create_state(window)
            if folder_path:
                state.panel.set_folder(folder_path)

            toggle_item = Nemo.MenuItem(
                name="NemoTodo::TogglePanel",
                label="Toggle TODO Panel",
                tip="Show or hide the TODO panel",
            )
            toggle_item.connect("activate", self._toggle_panel, window)

            return [toggle_item]

        def get_widget(self, _uri, window):
            self._ensure_window_key_handler(window)
            widget = Gtk.EventBox()
            widget.set_no_show_all(True)
            widget.hide()
            return widget

        def get_file_items(self, window, files):
            return []

        def _toggle_panel(self, _menu, window):
            state = self.window_states.get(window)
            if state:
                state.panel.toggle_visible()

        def _on_window_key_press(self, window, event):
            accelerator = self.settings.get_string("panel-hotkey")
            keyval, modifiers = Gtk.accelerator_parse(accelerator)
            if not keyval:
                return False

            mask = Gtk.accelerator_get_default_mod_mask()
            if event.keyval != keyval or (event.state & mask) != (modifiers & mask):
                return False

            state = self._get_or_create_state(window)
            state.panel.toggle_visible()
            return True

        def _on_todo_window_key_press(self, _todo_window, event, nemo_window):
            return self._on_window_key_press(nemo_window, event)

        def _ensure_window_key_handler(self, window):
            if window not in self.key_windows:
                window.connect("key-press-event", self._on_window_key_press)
                self.key_windows.add(window)

        def _get_or_create_state(self, window):
            state = self.window_states.get(window)
            if state is not None:
                return state

            self._ensure_window_key_handler(window)

            panel_class = WebTodoPanel if WebKit2 is not None else TodoPanel
            try:
                panel = panel_class(self.todo_service, self.table_service)
            except Exception:
                if panel_class is TodoPanel:
                    raise
                logger.exception("Unable to start WebKit TODO panel; using GTK fallback")
                panel_class = TodoPanel
                panel = panel_class(self.todo_service, self.table_service)
            todo_window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
            todo_window.set_title("Nemo TODO")
            todo_window.set_default_size(panel_class.DEFAULT_WIDTH, 700)
            todo_window.set_transient_for(window)
            todo_window.set_destroy_with_parent(True)
            todo_window.add(panel.widget())
            panel.set_window(todo_window)
            panel.hide()
            todo_window.connect("key-press-event", self._on_todo_window_key_press, window)
            todo_window.connect("delete-event", self._hide_window, panel)
            state = _WindowState(panel, todo_window)
            self.window_states[window] = state
            return state

        @staticmethod
        def _hide_window(window, _event, panel):
            panel.hide()
            return True

        def _uri_to_path(self, uri: str) -> str:
            return normalize_folder_path(uri)

        def _folder_from_selected_files(self, files) -> str | None:
            try:
                resolved_folders = set()
                for file_info in files:
                    folder = self._folder_for_file_info(file_info)
                    if not folder:
                        return None
                    resolved_folders.add(folder)
                if len(resolved_folders) == 1:
                    return next(iter(resolved_folders))
            except Exception:
                logger.exception("Unable to resolve selected file folder")
            return None

        def _folder_for_file_info(self, file_info) -> str | None:
            if file_info.is_directory():
                return normalize_folder_path(file_info.get_uri())
            parent = file_info.get_parent_info()
            if parent is not None:
                return normalize_folder_path(parent.get_uri())
            return None

else:

    class NemoTodoExtension:  # pragma: no cover
        def __init__(self):
            raise RuntimeError("Nemo bindings are unavailable")
