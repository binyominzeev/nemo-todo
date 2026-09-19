import os
import tempfile
import unittest

from core.nemo_todo_core.database import Database
from core.nemo_todo_core.todo_service import TodoService


class TodoServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.tmp.name, "todo.db"))
        self.db.initialize()
        self.service = TodoService(self.db)
        self.folder = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_toggle_and_order_tasks(self):
        t1 = self.service.create_task(self.folder, "first")
        t2 = self.service.create_task(self.folder, "second")

        tasks = self.service.list_tasks(self.folder)
        self.assertEqual(["first", "second"], [t.text for t in tasks])

        self.service.set_task_completed(t1.id, True)
        tasks = self.service.list_tasks(self.folder)
        self.assertTrue(tasks[0].completed)

        self.service.reorder_tasks(self.folder, [t2.id, t1.id])
        tasks = self.service.list_tasks(self.folder)
        self.assertEqual([t2.id, t1.id], [t.id for t in tasks])

    def test_delete_reindexes_positions(self):
        t1 = self.service.create_task(self.folder, "one")
        t2 = self.service.create_task(self.folder, "two")
        self.service.delete_task(t1.id)
        tasks = self.service.list_tasks(self.folder)
        self.assertEqual([t2.id], [t.id for t in tasks])
        self.assertEqual(1, tasks[0].position)

    def test_reorder_with_partial_list_keeps_remaining_and_does_not_mutate_input(self):
        t1 = self.service.create_task(self.folder, "one")
        t2 = self.service.create_task(self.folder, "two")
        t3 = self.service.create_task(self.folder, "three")
        order = [t3.id]

        self.service.reorder_tasks(self.folder, order)

        self.assertEqual([t3.id], order)
        tasks = self.service.list_tasks(self.folder)
        self.assertEqual([t3.id, t1.id, t2.id], [t.id for t in tasks])

    def test_reorder_ignores_duplicate_and_foreign_ids(self):
        t1 = self.service.create_task(self.folder, "one")
        t2 = self.service.create_task(self.folder, "two")
        t3 = self.service.create_task(self.folder, "three")
        other_folder = os.path.join(self.tmp.name, "other")
        os.makedirs(other_folder, exist_ok=True)
        foreign = self.service.create_task(other_folder, "other")

        self.service.reorder_tasks(self.folder, [t3.id, t3.id, foreign.id, t1.id])

        tasks = self.service.list_tasks(self.folder)
        self.assertEqual([t3.id, t1.id, t2.id], [t.id for t in tasks])
        self.assertEqual([1, 2, 3], [t.position for t in tasks])


if __name__ == "__main__":
    unittest.main()
