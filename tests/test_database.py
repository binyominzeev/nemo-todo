import os
import sqlite3
import tempfile
import unittest

from src.database import Database, SCHEMA_VERSION


class DatabaseTests(unittest.TestCase):
    def test_initialize_creates_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "todo.db")
            db = Database(db_path)
            db.initialize()

            with db.connect() as conn:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                self.assertEqual(SCHEMA_VERSION, version)
                tables = {
                    r[0]
                    for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                self.assertTrue({"folders", "tasks", "tables", "table_rows", "table_columns", "table_cells"}.issubset(tables))

    def test_initialize_rejects_newer_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "todo.db")
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA user_version = 999")
            conn.close()

            db = Database(db_path)
            with self.assertRaises(RuntimeError):
                db.initialize()


if __name__ == "__main__":
    unittest.main()
