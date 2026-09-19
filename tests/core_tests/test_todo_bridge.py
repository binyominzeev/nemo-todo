import os
import tempfile
import unittest

from core.nemo_todo_core.database import Database
from core.nemo_todo_core.table_service import TableService
from core.nemo_todo_core.todo_bridge import TodoBridge, TodoBridgeError
from core.nemo_todo_core.todo_service import TodoService


class TodoBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        database = Database(os.path.join(self.tmp.name, "todo.db"))
        database.initialize()
        self.bridge = TodoBridge(TodoService(database), TableService(database))
        self.bridge.set_folder(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_toggle_task_returns_serialized_state(self):
        state = self.bridge.execute("create_task", {"text": "Film 1"})
        task = state["tasks"][0]
        self.assertEqual("Film 1", task["text"])

        state = self.bridge.execute("toggle_task", {"task_id": task["id"], "completed": True})
        self.assertTrue(state["tasks"][0]["completed"])

    def test_table_state_contains_rows_columns_and_cells(self):
        state = self.bridge.execute("create_table", {"name": "Video"})
        table_id = state["tables"][0]["id"]
        state = self.bridge.execute("create_row", {"table_id": table_id, "name": "001"})
        row_id = state["tables"][0]["rows"][0]["id"]
        state = self.bridge.execute("create_column", {"table_id": table_id, "name": "Upload"})
        column_id = state["tables"][0]["columns"][0]["id"]

        state = self.bridge.execute(
            "toggle_cell", {"row_id": row_id, "column_id": column_id, "completed": True}
        )
        self.assertEqual({"row_id": row_id, "column_id": column_id, "completed": True}, state["tables"][0]["cells"][0])

    def test_rejects_unknown_command_and_invalid_payload(self):
        with self.assertRaises(TodoBridgeError):
            self.bridge.execute("unknown")
        with self.assertRaises(TodoBridgeError):
            self.bridge.execute("create_task", {"text": "  "})
        with self.assertRaises(TodoBridgeError):
            self.bridge.execute("toggle_task", {"task_id": True, "completed": False})

    def test_folder_is_required(self):
        bridge = TodoBridge(self.bridge.todo_service, self.bridge.table_service)
        with self.assertRaises(TodoBridgeError):
            bridge.get_state()


if __name__ == "__main__":
    unittest.main()
