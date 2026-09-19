"""X11-only docking hack: snaps the standalone Dolphin panel beside the Dolphin window."""

import logging

from platforms.linux.common.dock_geometry import Geometry, compute_dock_geometry

logger = logging.getLogger(__name__)

try:
    from Xlib import X
    from Xlib.display import Display
    from Xlib.error import XError
    from Xlib.protocol.event import ClientMessage
except Exception:  # pragma: no cover
    X = None
    Display = None
    XError = Exception
    ClientMessage = None

try:
    from gi.repository import GLib
except Exception:  # pragma: no cover
    GLib = None

_NET_ACTIVE_WINDOW = "_NET_ACTIVE_WINDOW"
_NET_CLIENT_LIST = "_NET_CLIENT_LIST"
_NET_MOVERESIZE_WINDOW = "_NET_MOVERESIZE_WINDOW"
_MOVERESIZE_WIDTH_HEIGHT_FLAGS = (1 << 10) | (1 << 11)  # width + height present, keep gravity/x/y untouched


def open_display():
    if Display is None:
        return None
    try:
        return Display()
    except Exception:
        logger.debug("No X11 display available", exc_info=True)
        return None


def is_x11_available() -> bool:
    display = open_display()
    if display is None:
        return False
    display.close()
    return True


def _window_property(display, window, atom_name):
    atom = display.intern_atom(atom_name)
    try:
        prop = window.get_full_property(atom, X.AnyPropertyType)
    except XError:
        return None
    if prop is None:
        return None
    return prop.value


def _is_dolphin_window(window) -> bool:
    try:
        wm_class = window.get_wm_class()
    except XError:
        return False
    if not wm_class:
        return False
    return any("dolphin" in part.lower() for part in wm_class)


def find_active_dolphin_window(display):
    """Heuristic: prefer the currently active window, then scan the client list."""
    root = display.screen().root
    active_ids = _window_property(display, root, _NET_ACTIVE_WINDOW)
    if active_ids:
        window = display.create_resource_object("window", active_ids[0])
        if _is_dolphin_window(window):
            return window

    client_ids = _window_property(display, root, _NET_CLIENT_LIST) or []
    for window_id in client_ids:
        window = display.create_resource_object("window", window_id)
        if _is_dolphin_window(window):
            return window
    return None


def get_geometry(display, window) -> Geometry:
    root = display.screen().root
    geom = window.get_geometry()
    coords = window.translate_coords(root, 0, 0)
    return Geometry(x=coords.x, y=coords.y, width=geom.width, height=geom.height)


def request_resize(display, window, width, height):
    """Ask the window manager to resize a foreign top-level window (EWMH _NET_MOVERESIZE_WINDOW)."""
    root = display.screen().root
    atom = display.intern_atom(_NET_MOVERESIZE_WINDOW)
    event = ClientMessage(
        window=window,
        client_type=atom,
        data=(32, (_MOVERESIZE_WIDTH_HEIGHT_FLAGS, 0, 0, width, height)),
    )
    root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    display.flush()


class DockTracker:
    """Keeps the panel beside the Dolphin window and mirrors height changes both ways.

    Width is "sticky": once the user resizes the panel, its width is kept on
    subsequent Dolphin moves/resizes. Height is treated as a single shared
    dimension: whichever window's height changes last "wins" and is mirrored
    onto the other one, so the pair behaves like a single docked window.
    """

    def __init__(self, display, dolphin_window, todo_window, panel_width, on_closed=None):
        self.display = display
        self.dolphin_window = dolphin_window
        self.todo_window = todo_window
        self.panel_width = panel_width
        self.on_closed = on_closed
        self._source_id = None
        self._last_dolphin_height = None
        self._last_todo_size = None
        self.dolphin_window.change_attributes(event_mask=X.StructureNotifyMask)
        self.todo_window.connect("configure-event", self._on_todo_window_configured)

    def start(self):
        if GLib is None or self._source_id is not None:
            return
        self._source_id = GLib.io_add_watch(self.display.fileno(), GLib.IO_IN, self._on_display_readable)

    def stop(self):
        if self._source_id is not None:
            GLib.source_remove(self._source_id)
            self._source_id = None

    def _on_display_readable(self, *_args):
        while self.display.pending_events():
            event = self.display.next_event()
            if getattr(event, "window", None) != self.dolphin_window:
                continue
            if event.type == X.ConfigureNotify:
                self.reposition()
            elif event.type == X.DestroyNotify:
                self._handle_closed()
        return True

    def reposition(self):
        geom = get_geometry(self.display, self.dolphin_window)
        dolphin_height_changed = self._last_dolphin_height is None or geom.height != self._last_dolphin_height
        self._last_dolphin_height = geom.height
        if dolphin_height_changed or self._last_todo_size is None:
            height = geom.height
        else:
            height = self._last_todo_size[1]

        screen_width = self.display.screen().width_in_pixels
        dock = compute_dock_geometry(geom, self.panel_width, screen_width)
        self.todo_window.move(dock.x, dock.y)
        self.todo_window.resize(dock.width, height)
        self._last_todo_size = (dock.width, height)

    def _on_todo_window_configured(self, _widget, _event):
        width, height = self.todo_window.get_size()
        if self._last_todo_size == (width, height):
            return False
        self.panel_width = width
        self._last_todo_size = (width, height)
        self._mirror_height_to_dolphin(height)
        return False

    def _mirror_height_to_dolphin(self, height):
        geom = get_geometry(self.display, self.dolphin_window)
        if height == geom.height:
            return
        self._last_dolphin_height = height
        request_resize(self.display, self.dolphin_window, geom.width, height)

    def _handle_closed(self):
        self.stop()
        if self.on_closed is not None:
            self.on_closed()

