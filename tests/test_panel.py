import unittest

from src import panel as panel_module


class _VisibleStub:
    def __init__(self):
        self.last_visible = True

    def set_visible(self, visible):
        self.last_visible = visible


class _EventStub:
    def __init__(self, keyval, state):
        self.keyval = keyval
        self.state = state


class PanelBehaviorTests(unittest.TestCase):
    def test_toggle_visible_updates_flag_and_widget_visibility(self):
        panel = panel_module.TodoPanel.__new__(panel_module.TodoPanel)
        panel.visible = True
        panel.container = _VisibleStub()

        panel.toggle_visible()
        self.assertFalse(panel.visible)
        self.assertFalse(panel.container.last_visible)

        panel.toggle_visible()
        self.assertTrue(panel.visible)
        self.assertTrue(panel.container.last_visible)

    @unittest.skipIf(panel_module.Gdk is None, "Gdk unavailable")
    def test_shortcut_handler_accepts_lowercase_and_uppercase_t(self):
        panel = panel_module.TodoPanel.__new__(panel_module.TodoPanel)
        panel.visible = True
        panel.container = _VisibleStub()
        panel.toggle_visible = lambda: setattr(panel, "visible", not panel.visible)

        mask = panel_module.Gdk.ModifierType.CONTROL_MASK | panel_module.Gdk.ModifierType.MOD1_MASK
        handled_lower = panel._on_key_press(None, _EventStub(panel_module.Gdk.KEY_t, mask))
        handled_upper = panel._on_key_press(None, _EventStub(panel_module.Gdk.KEY_T, mask))

        self.assertTrue(handled_lower)
        self.assertTrue(handled_upper)


if __name__ == "__main__":
    unittest.main()
