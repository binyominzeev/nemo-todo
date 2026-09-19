import unittest
from unittest.mock import MagicMock

from platforms.linux.nemo import nemo_todo_extension as extension_module


def _make_state(panel_width=400):
    return extension_module._WindowState(panel=None, todo_window=MagicMock(), panel_width=panel_width)


class RepositionTodoWindowTests(unittest.TestCase):
    def _make_nemo_window(self, position, size, screen_width=1920):
        nemo_window = MagicMock()
        nemo_window.get_position.return_value = position
        nemo_window.get_size.return_value = size
        nemo_window.get_screen.return_value.get_width.return_value = screen_width
        return nemo_window

    def test_docks_todo_window_to_the_right_of_nemo_window(self):
        extension = extension_module.NemoTodoExtension.__new__(extension_module.NemoTodoExtension)
        nemo_window = self._make_nemo_window(position=(100, 50), size=(800, 600))
        state = _make_state(panel_width=400)

        extension._reposition_todo_window(nemo_window, state)

        state.todo_window.move.assert_called_once_with(900, 50)
        state.todo_window.resize.assert_called_once_with(400, 600)

    def test_flips_to_the_left_when_right_side_overflows(self):
        extension = extension_module.NemoTodoExtension.__new__(extension_module.NemoTodoExtension)
        nemo_window = self._make_nemo_window(position=(1200, 0), size=(800, 600))
        state = _make_state(panel_width=400)

        extension._reposition_todo_window(nemo_window, state)

        state.todo_window.move.assert_called_once_with(800, 0)

    def test_move_only_keeps_previously_applied_todo_height(self):
        extension = extension_module.NemoTodoExtension.__new__(extension_module.NemoTodoExtension)
        nemo_window = self._make_nemo_window(position=(100, 50), size=(800, 600))
        state = _make_state(panel_width=400)
        extension._reposition_todo_window(nemo_window, state)

        # user shrunk the panel height manually in between
        state.last_todo_size = (400, 300)
        nemo_window.get_position.return_value = (150, 50)

        extension._reposition_todo_window(nemo_window, state)

        state.todo_window.resize.assert_called_with(400, 300)

    def test_nemo_resize_overrides_sticky_todo_height(self):
        extension = extension_module.NemoTodoExtension.__new__(extension_module.NemoTodoExtension)
        nemo_window = self._make_nemo_window(position=(100, 50), size=(800, 600))
        state = _make_state(panel_width=400)
        extension._reposition_todo_window(nemo_window, state)
        state.last_todo_size = (400, 300)

        nemo_window.get_size.return_value = (800, 700)
        extension._reposition_todo_window(nemo_window, state)

        state.todo_window.resize.assert_called_with(400, 700)

    def test_height_only_mirror_does_not_move_when_nemo_stays_put(self):
        extension = extension_module.NemoTodoExtension.__new__(extension_module.NemoTodoExtension)
        nemo_window = self._make_nemo_window(position=(100, 50), size=(800, 600))
        state = _make_state(panel_width=400)
        extension._reposition_todo_window(nemo_window, state)
        state.todo_window.move.reset_mock()

        # Nemo's height changed (e.g. mirrored from the panel's own resize) but it did not move.
        nemo_window.get_size.return_value = (800, 700)
        extension._reposition_todo_window(nemo_window, state)

        state.todo_window.move.assert_not_called()
        state.todo_window.resize.assert_called_with(400, 700)

    def test_manual_todo_resize_updates_sticky_width_and_mirrors_height(self):
        extension = extension_module.NemoTodoExtension.__new__(extension_module.NemoTodoExtension)
        nemo_window = MagicMock()
        nemo_window.get_size.return_value = (800, 600)
        state = _make_state(panel_width=400)
        state.last_todo_size = (400, 600)
        state.todo_window.get_size.return_value = (350, 700)

        extension._on_todo_window_configured(state.todo_window, None, nemo_window, state)

        self.assertEqual(350, state.panel_width)
        nemo_window.resize.assert_called_once_with(800, 700)


if __name__ == "__main__":
    unittest.main()

