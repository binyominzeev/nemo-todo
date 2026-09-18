from .database import Database
from .models import Task
from .path_utils import normalize_folder_path


class TodoService:
    def __init__(self, database: Database):
        self.database = database

    def ensure_folder(self, folder: str) -> int:
        normalized = normalize_folder_path(folder)
        with self.database.connect() as conn:
            row = conn.execute("SELECT id FROM folders WHERE path = ?", (normalized,)).fetchone()
            if row:
                return row["id"]
            cursor = conn.execute("INSERT INTO folders(path) VALUES(?)", (normalized,))
            return cursor.lastrowid

    def list_tasks(self, folder: str) -> list[Task]:
        folder_id = self.ensure_folder(folder)
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, folder_id, text, completed, position, created_at
                FROM tasks
                WHERE folder_id = ?
                ORDER BY position ASC, id ASC
                """,
                (folder_id,),
            ).fetchall()
            return [
                Task(
                    id=row["id"],
                    folder_id=row["folder_id"],
                    text=row["text"],
                    completed=bool(row["completed"]),
                    position=row["position"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    def create_task(self, folder: str, text: str) -> Task:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Task text cannot be empty")

        folder_id = self.ensure_folder(folder)
        with self.database.connect() as conn:
            max_position = conn.execute(
                "SELECT COALESCE(MAX(position), 0) FROM tasks WHERE folder_id = ?", (folder_id,)
            ).fetchone()[0]
            cursor = conn.execute(
                "INSERT INTO tasks(folder_id, text, completed, position) VALUES(?, ?, 0, ?)",
                (folder_id, cleaned, max_position + 1),
            )
            row = conn.execute(
                "SELECT id, folder_id, text, completed, position, created_at FROM tasks WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
            return Task(
                id=row["id"],
                folder_id=row["folder_id"],
                text=row["text"],
                completed=bool(row["completed"]),
                position=row["position"],
                created_at=row["created_at"],
            )

    def set_task_completed(self, task_id: int, completed: bool) -> None:
        with self.database.connect() as conn:
            conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (1 if completed else 0, task_id))

    def update_task_text(self, task_id: int, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Task text cannot be empty")
        with self.database.connect() as conn:
            conn.execute("UPDATE tasks SET text = ? WHERE id = ?", (cleaned, task_id))

    def delete_task(self, task_id: int) -> None:
        with self.database.connect() as conn:
            row = conn.execute("SELECT folder_id, position FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                return
            folder_id = row["folder_id"]
            position = row["position"]
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.execute(
                "UPDATE tasks SET position = position - 1 WHERE folder_id = ? AND position > ?",
                (folder_id, position),
            )

    def reorder_tasks(self, folder: str, ordered_task_ids: list[int]) -> None:
        folder_id = self.ensure_folder(folder)
        if not ordered_task_ids:
            return
        with self.database.connect() as conn:
            existing = conn.execute(
                "SELECT id FROM tasks WHERE folder_id = ? ORDER BY position ASC, id ASC", (folder_id,)
            ).fetchall()
            existing_ids = [row["id"] for row in existing]
            for task_id in existing_ids:
                if task_id not in ordered_task_ids:
                    ordered_task_ids.append(task_id)
            for index, task_id in enumerate(ordered_task_ids, start=1):
                conn.execute(
                    "UPDATE tasks SET position = ? WHERE id = ? AND folder_id = ?",
                    (index, task_id, folder_id),
                )
