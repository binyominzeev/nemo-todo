import unittest

from platforms.linux.nemo import panel as panel_module


class _VisibleStub:
    def __init__(self):
        self.last_visible = True

    def set_visible(self, visible):
        self.last_visible = visible


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

if __name__ == "__main__":
    unittest.main()
