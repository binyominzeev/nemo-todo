import os
import tempfile
import unittest

from core.nemo_todo_core.database import Database
from core.nemo_todo_core.table_service import TableService


class TableServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.tmp.name, "todo.db"))
        self.db.initialize()
        self.service = TableService(self.db)
        self.folder = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_table_rows_columns_and_toggle_cell(self):
        table = self.service.create_table(self.folder, "Video")
        row = self.service.create_row(table.id, "001")
        col = self.service.create_column(table.id, "Upload")

        toggled = self.service.toggle_cell(row.id, col.id)
        self.assertTrue(toggled.completed)

        snapshots = self.service.list_tables(self.folder)
        self.assertEqual(1, len(snapshots))
        snapshot = snapshots[0]
        self.assertEqual("Video", snapshot.table.name)
        self.assertEqual(True, snapshot.cells[(row.id, col.id)])

    def test_reorder_rows_and_columns(self):
        table = self.service.create_table(self.folder, "Checklist")
        row1 = self.service.create_row(table.id, "r1")
        row2 = self.service.create_row(table.id, "r2")
        col1 = self.service.create_column(table.id, "c1")
        col2 = self.service.create_column(table.id, "c2")

        self.service.reorder_rows(table.id, [row2.id, row1.id])
        self.service.reorder_columns(table.id, [col2.id, col1.id])

        snapshot = self.service.list_tables(self.folder)[0]
        self.assertEqual([row2.id, row1.id], [r.id for r in snapshot.rows])
        self.assertEqual([col2.id, col1.id], [c.id for c in snapshot.columns])

    def test_partial_reorder_does_not_mutate_input(self):
        table = self.service.create_table(self.folder, "Checklist")
        row1 = self.service.create_row(table.id, "r1")
        row2 = self.service.create_row(table.id, "r2")
        row3 = self.service.create_row(table.id, "r3")
        col1 = self.service.create_column(table.id, "c1")
        col2 = self.service.create_column(table.id, "c2")
        col3 = self.service.create_column(table.id, "c3")

        row_order = [row3.id]
        col_order = [col3.id]
        self.service.reorder_rows(table.id, row_order)
        self.service.reorder_columns(table.id, col_order)

        self.assertEqual([row3.id], row_order)
        self.assertEqual([col3.id], col_order)
        snapshot = self.service.list_tables(self.folder)[0]
        self.assertEqual([row3.id, row1.id, row2.id], [r.id for r in snapshot.rows])
        self.assertEqual([col3.id, col1.id, col2.id], [c.id for c in snapshot.columns])

    def test_reorder_ignores_duplicate_and_foreign_ids(self):
        table = self.service.create_table(self.folder, "Checklist")
        row1 = self.service.create_row(table.id, "r1")
        row2 = self.service.create_row(table.id, "r2")
        row3 = self.service.create_row(table.id, "r3")
        col1 = self.service.create_column(table.id, "c1")
        col2 = self.service.create_column(table.id, "c2")
        col3 = self.service.create_column(table.id, "c3")

        table2 = self.service.create_table(self.folder, "Other")
        foreign_row = self.service.create_row(table2.id, "fr")
        foreign_col = self.service.create_column(table2.id, "fc")

        self.service.reorder_rows(table.id, [row3.id, row3.id, foreign_row.id, row1.id])
        self.service.reorder_columns(table.id, [col3.id, col3.id, foreign_col.id, col1.id])

        snapshot = self.service.list_tables(self.folder)[0]
        self.assertEqual([row3.id, row1.id, row2.id], [r.id for r in snapshot.rows])
        self.assertEqual([1, 2, 3], [r.position for r in snapshot.rows])
        self.assertEqual([col3.id, col1.id, col2.id], [c.id for c in snapshot.columns])
        self.assertEqual([1, 2, 3], [c.position for c in snapshot.columns])

    def test_rejects_cross_table_cells(self):
        table1 = self.service.create_table(self.folder, "t1")
        table2 = self.service.create_table(self.folder, "t2")
        row = self.service.create_row(table1.id, "r1")
        col = self.service.create_column(table2.id, "c1")

        with self.assertRaises(ValueError):
            self.service.set_cell_completed(row.id, col.id, True)


if __name__ == "__main__":
    unittest.main()
