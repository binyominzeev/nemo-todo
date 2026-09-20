import json
import logging
from pathlib import Path

from core.nemo_todo_core.todo_bridge import TodoBridge, TodoBridgeError

logger = logging.getLogger(__name__)

try:
    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("Gtk", "3.0")
    gi.require_version("WebKit2", "4.0")
    from gi.repository import Gdk, GLib, Gtk, WebKit2
except Exception:  # pragma: no cover
    Gdk = None
    GLib = None
    Gtk = None
    WebKit2 = None


class WebTodoPanel:
    DEFAULT_WIDTH = 920

    def __init__(self, todo_service, table_service):
        if WebKit2 is None or Gtk is None:
            raise RuntimeError("WebKitGTK is unavailable")
        self.bridge = TodoBridge(todo_service, table_service)
        self.current_folder = None
        self.visible = True
        self.window = None

        manager = WebKit2.UserContentManager()
        manager.register_script_message_handler("nemo")
        manager.connect("script-message-received::nemo", self._on_script_message)
        self.webview = WebKit2.WebView.new_with_user_content_manager(manager)
        self.webview.set_hexpand(True)
        self.webview.set_vexpand(True)
        settings = self.webview.get_settings()
        settings.set_property("enable-javascript", True)
        settings.set_property("enable-html5-local-storage", True)
        settings.set_property("allow-file-access-from-file-urls", True)
        settings.set_property("allow-universal-access-from-file-urls", True)
        self.webview.connect("load-changed", self._on_load_changed)

        web_root = Path(__file__).resolve().parents[3] / "frontend"
        self.webview.load_uri(GLib.filename_to_uri(str(web_root / "index.html"), None))

    def widget(self):
        return self.webview

    def set_window(self, window):
        self.window = window

    def show(self):
        self.visible = True
        self.webview.set_visible(True)
        if self.window is not None:
            self.window.show_all()

    def hide(self):
        self.visible = False
        self.webview.set_visible(False)
        if self.window is not None:
            self.window.hide()

    def toggle_visible(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def set_folder(self, folder_path: str):
        if folder_path == self.current_folder:
            return
        self.current_folder = folder_path
        self.bridge.set_folder(folder_path)
        self.reload()

    def reload(self):
        if not self.current_folder:
            return
        self._send_state()

    def _on_load_changed(self, _webview, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            self._send_state()

    def _send_state(self):
        try:
            state = self.bridge.get_state()
        except TodoBridgeError as error:
            self._send_error(str(error))
            return
        script = "window.nemoTodoReceive(%s);" % json.dumps(state)
        self.webview.run_javascript(script, None, None, None)

    def _send_error(self, message):
        script = "window.nemoTodoError(%s);" % json.dumps(message)
        self.webview.run_javascript(script, None, None, None)

    def _on_script_message(self, _manager, message):
        try:
            request = json.loads(message.get_js_value().to_string())
            command = request.get("command")
            payload = request.get("payload", {})
            state = self.bridge.execute(command, payload)
            script = "window.nemoTodoReceive(%s);" % json.dumps(state)
            self.webview.run_javascript(script, None, None, None)
        except (TodoBridgeError, ValueError, TypeError, KeyError) as error:
            logger.warning("Web TODO command failed: %s", error)
            self._send_error(str(error))
