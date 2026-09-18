import os
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1


class Database:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(Path.home() / ".local/share/nemo-todo/todo.db")

    def initialize(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self.connect() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                self._apply_schema_v1(conn)
                conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            elif version > SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database version {version} is newer than supported version {SCHEMA_VERSION}"
                )

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _apply_schema_v1(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                position INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY(folder_id) REFERENCES folders(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS table_columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY(table_id) REFERENCES tables(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS table_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY(table_id) REFERENCES tables(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS table_cells (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                row_id INTEGER NOT NULL,
                column_id INTEGER NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                UNIQUE(row_id, column_id),
                FOREIGN KEY(row_id) REFERENCES table_rows(id) ON DELETE CASCADE,
                FOREIGN KEY(column_id) REFERENCES table_columns(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path);
            CREATE INDEX IF NOT EXISTS idx_tasks_folder_position ON tasks(folder_id, position);
            CREATE INDEX IF NOT EXISTS idx_tables_folder_position ON tables(folder_id, position);
            CREATE INDEX IF NOT EXISTS idx_columns_table_position ON table_columns(table_id, position);
            CREATE INDEX IF NOT EXISTS idx_rows_table_position ON table_rows(table_id, position);
            CREATE INDEX IF NOT EXISTS idx_cells_row_col ON table_cells(row_id, column_id);
            """
        )
