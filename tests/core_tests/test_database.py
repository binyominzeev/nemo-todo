import os
import sqlite3
import tempfile
import unittest

from core.nemo_todo_core.database import Database, SCHEMA_VERSION


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
                self.assertTrue(
                    {"folders", "tasks", "tables", "table_rows", "table_columns", "table_cells", "schema_migrations"}.issubset(
                        tables
                    )
                )

    def test_initialize_rejects_newer_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "todo.db")
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA user_version = 999")
            conn.close()

            db = Database(db_path)
            with self.assertRaises(RuntimeError):
                db.initialize()

    def test_initialize_supports_relative_db_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                db = Database("todo.db")
                db.initialize()
                self.assertTrue(os.path.exists("todo.db"))
            finally:
                os.chdir(cwd)

    def test_initialize_upgrades_from_schema_v1(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "todo.db")
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA user_version = 1")
            conn.execute("CREATE TABLE folders(id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL UNIQUE)")
            conn.commit()
            conn.close()

            db = Database(db_path)
            db.initialize()
            with db.connect() as check_conn:
                version = check_conn.execute("PRAGMA user_version").fetchone()[0]
                self.assertEqual(SCHEMA_VERSION, version)
                migration_table = check_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
                ).fetchone()
                self.assertIsNotNone(migration_table)


if __name__ == "__main__":
    unittest.main()
