import logging
from urllib.parse import urlparse

from .database import Database
from .panel import TodoPanel
from .path_utils import normalize_folder_path
from .table_service import TableService
from .todo_service import TodoService

logger = logging.getLogger(__name__)

try:
    import gi

    gi.require_version("Nemo", "3.0")
    from gi.repository import GObject, Nemo
except Exception:  # pragma: no cover
    GObject = None
    Nemo = None


class _WindowState:
    def __init__(self, panel: TodoPanel):
        self.panel = panel


if GObject is not None and Nemo is not None:

    class NemoTodoExtension(GObject.GObject, Nemo.LocationWidgetProvider, Nemo.MenuProvider, Nemo.NameAndDescProvider):
        def __init__(self):
            super().__init__()
            self.database = Database()
            self.database.initialize()
            self.todo_service = TodoService(self.database)
            self.table_service = TableService(self.database)
            self.window_states = {}

        def get_name_and_desc(self):
            return ("Nemo TODO", "Folder-aware TODO and checklist panel")

        def get_widget(self, uri, window):
            try:
                state = self.window_states.get(window)
                if state is None:
                    panel = TodoPanel(self.todo_service, self.table_service)
                    state = _WindowState(panel)
                    self.window_states[window] = state
                folder_path = self._uri_to_path(uri)
                state.panel.set_folder(folder_path)
                return state.panel.widget()
            except Exception:  # pragma: no cover
                logger.exception("Failed to build Nemo TODO panel")
                return None

        def get_background_items(self, window, current_folder):
            if current_folder is None:
                return
            folder_path = None
            try:
                folder_path = normalize_folder_path(current_folder.get_uri())
            except Exception:
                logger.exception("Unable to resolve current folder from Nemo")

            toggle_item = Nemo.MenuItem(
                name="NemoTodo::TogglePanel",
                label="Toggle TODO Panel",
                tip="Show or hide the TODO panel",
            )
            toggle_item.connect("activate", self._toggle_panel, window)

            add_item = Nemo.MenuItem(
                name="NemoTodo::AddTodo",
                label="Add TODO",
                tip="Create a TODO for this folder",
            )
            add_item.connect("activate", self._add_todo, window, folder_path)
            return [toggle_item, add_item]

        def get_file_items(self, window, files):
            if not files:
                return
            folder_path = self._folder_from_selected_files(files)
            if not folder_path:
                return
            add_item = Nemo.MenuItem(
                name="NemoTodo::AddTodoFile",
                label="Add TODO",
                tip="Create a TODO for this folder",
            )
            add_item.connect("activate", self._add_todo, window, folder_path)
            return [add_item]

        def _toggle_panel(self, _menu, window):
            state = self.window_states.get(window)
            if state:
                state.panel.toggle_visible()

        def _add_todo(self, _menu, window, folder_path=None):
            state = self.window_states.get(window)
            target_folder = folder_path or (state.panel.current_folder if state else None)
            if target_folder:
                self.todo_service.create_task(target_folder, "New TODO")
            if state:
                state.panel.reload()

        def _uri_to_path(self, uri: str) -> str:
            parsed = urlparse(uri)
            if parsed.scheme != "file":
                raise ValueError(f"Unsupported URI: {uri}")
            return normalize_folder_path(uri)

        def _folder_from_selected_files(self, files) -> str | None:
            try:
                first = files[0]
                if first.is_directory():
                    return normalize_folder_path(first.get_uri())
                parent = first.get_parent_info()
                if parent is not None:
                    return normalize_folder_path(parent.get_uri())
            except Exception:
                logger.exception("Unable to resolve selected file folder")
            return None

else:

    class NemoTodoExtension:  # pragma: no cover
        def __init__(self):
            raise RuntimeError("Nemo bindings are unavailable")
