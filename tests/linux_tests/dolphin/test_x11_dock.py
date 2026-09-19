import unittest
from unittest.mock import MagicMock

from platforms.linux.dolphin import x11_dock


class _StubProperty:
    def __init__(self, value):
        self.value = value


def _make_window(wm_class=None):
    window = MagicMock()
    window.get_wm_class.return_value = wm_class
    return window


class FindActiveDolphinWindowTests(unittest.TestCase):
    def _make_display(self, active_id, client_ids, windows_by_id):
        display = MagicMock()
        display.intern_atom.side_effect = lambda name: name
        root = MagicMock()
        display.screen.return_value.root = root

        def get_full_property(atom, _type):
            if atom == x11_dock._NET_ACTIVE_WINDOW:
                return _StubProperty([active_id]) if active_id is not None else None
            if atom == x11_dock._NET_CLIENT_LIST:
                return _StubProperty(client_ids)
            return None

        root.get_full_property.side_effect = get_full_property
        display.create_resource_object.side_effect = lambda _kind, window_id: windows_by_id[window_id]
        return display

    def test_prefers_active_window_when_it_is_dolphin(self):
        dolphin_window = _make_window(("dolphin", "org.kde.dolphin"))
        display = self._make_display(active_id=1, client_ids=[1], windows_by_id={1: dolphin_window})

        result = x11_dock.find_active_dolphin_window(display)

        self.assertIs(dolphin_window, result)

    def test_falls_back_to_client_list_when_active_window_is_not_dolphin(self):
        other_window = _make_window(("other-app", "OtherApp"))
        dolphin_window = _make_window(("dolphin", "org.kde.dolphin"))
        display = self._make_display(
            active_id=1, client_ids=[1, 2], windows_by_id={1: other_window, 2: dolphin_window}
        )

        result = x11_dock.find_active_dolphin_window(display)

        self.assertIs(dolphin_window, result)

    def test_returns_none_when_no_dolphin_window_found(self):
        other_window = _make_window(("other-app", "OtherApp"))
        display = self._make_display(active_id=1, client_ids=[1], windows_by_id={1: other_window})

        result = x11_dock.find_active_dolphin_window(display)

        self.assertIsNone(result)


def _make_tracker(dolphin_width=800, dolphin_height=600, panel_width=400):
    display = MagicMock()
    display.screen.return_value.width_in_pixels = 1920
    dolphin_window = MagicMock()
    dolphin_window.get_geometry.return_value = MagicMock(width=dolphin_width, height=dolphin_height)
    dolphin_window.translate_coords.return_value = MagicMock(x=100, y=50)
    todo_window = MagicMock()
    tracker = x11_dock.DockTracker(display, dolphin_window, todo_window, panel_width)
    return tracker, dolphin_window, todo_window


class DockTrackerRepositionTests(unittest.TestCase):
    def test_initial_reposition_moves_and_matches_dolphin_height(self):
        tracker, _dolphin_window, todo_window = _make_tracker()

        tracker.reposition()

        todo_window.move.assert_called_once_with(900, 50)
        todo_window.resize.assert_called_once_with(400, 600)

    def test_move_only_keeps_previously_applied_todo_height(self):
        tracker, dolphin_window, todo_window = _make_tracker()
        tracker.reposition()
        todo_window.reset_mock()

        # user shrunk the panel height manually in between
        tracker._last_todo_size = (400, 300)

        # Dolphin only moves; its own height is unchanged
        dolphin_window.translate_coords.return_value = MagicMock(x=200, y=50)
        tracker.reposition()

        todo_window.resize.assert_called_once_with(400, 300)

    def test_dolphin_resize_overrides_sticky_todo_height(self):
        tracker, dolphin_window, todo_window = _make_tracker()
        tracker.reposition()
        tracker._last_todo_size = (400, 300)

        dolphin_window.get_geometry.return_value = MagicMock(width=800, height=700)
        tracker.reposition()

        todo_window.resize.assert_called_with(400, 700)

    def test_manual_todo_resize_updates_sticky_width(self):
        tracker, _dolphin_window, todo_window = _make_tracker()
        tracker.reposition()
        todo_window.get_size.return_value = (350, 700)

        tracker._on_todo_window_configured(todo_window, None)

        self.assertEqual(350, tracker.panel_width)

    def test_own_resize_does_not_retrigger_mirroring(self):
        tracker, _dolphin_window, todo_window = _make_tracker()
        tracker.reposition()
        todo_window.get_size.return_value = tracker._last_todo_size

        result = tracker._on_todo_window_configured(todo_window, None)

        self.assertFalse(result)
        self.assertEqual(400, tracker.panel_width)


if __name__ == "__main__":
    unittest.main()
