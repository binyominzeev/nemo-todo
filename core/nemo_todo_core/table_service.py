from .database import Database
from .models import ChecklistTable, TableCell, TableColumn, TableRow, TableSnapshot
from .path_utils import normalize_folder_path


class TableService:
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

    def create_table(self, folder: str, name: str) -> ChecklistTable:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Table name cannot be empty")
        folder_id = self.ensure_folder(folder)
        with self.database.connect() as conn:
            position = conn.execute(
                "SELECT COALESCE(MAX(position), 0) FROM tables WHERE folder_id = ?", (folder_id,)
            ).fetchone()[0]
            cursor = conn.execute(
                "INSERT INTO tables(folder_id, name, position) VALUES(?, ?, ?)",
                (folder_id, cleaned, position + 1),
            )
            return ChecklistTable(cursor.lastrowid, folder_id, cleaned, position + 1)

    def list_tables(self, folder: str) -> list[TableSnapshot]:
        folder_id = self.ensure_folder(folder)
        with self.database.connect() as conn:
            table_rows = conn.execute(
                "SELECT id, folder_id, name, position FROM tables WHERE folder_id = ? ORDER BY position, id",
                (folder_id,),
            ).fetchall()
            snapshots: list[TableSnapshot] = []
            for row in table_rows:
                table = ChecklistTable(row["id"], row["folder_id"], row["name"], row["position"])
                snapshots.append(self._snapshot_for_table(conn, table))
            return snapshots

    def _snapshot_for_table(self, conn, table: ChecklistTable) -> TableSnapshot:
        rows = [
            TableRow(r["id"], r["table_id"], r["name"], r["position"])
            for r in conn.execute(
                "SELECT id, table_id, name, position FROM table_rows WHERE table_id = ? ORDER BY position, id",
                (table.id,),
            )
        ]
        columns = [
            TableColumn(c["id"], c["table_id"], c["name"], c["position"])
            for c in conn.execute(
                "SELECT id, table_id, name, position FROM table_columns WHERE table_id = ? ORDER BY position, id",
                (table.id,),
            )
        ]
        cell_rows = conn.execute(
            """
            SELECT row_id, column_id, completed
            FROM table_cells
            WHERE row_id IN (SELECT id FROM table_rows WHERE table_id = ?)
            """,
            (table.id,),
        ).fetchall()
        cells = {(c["row_id"], c["column_id"]): bool(c["completed"]) for c in cell_rows}
        return TableSnapshot(table=table, rows=rows, columns=columns, cells=cells)

    def rename_table(self, table_id: int, name: str) -> None:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Table name cannot be empty")
        with self.database.connect() as conn:
            conn.execute("UPDATE tables SET name = ? WHERE id = ?", (cleaned, table_id))

    def delete_table(self, table_id: int) -> None:
        with self.database.connect() as conn:
            row = conn.execute("SELECT folder_id, position FROM tables WHERE id = ?", (table_id,)).fetchone()
            if row is None:
                return
            conn.execute("DELETE FROM tables WHERE id = ?", (table_id,))
            conn.execute(
                "UPDATE tables SET position = position - 1 WHERE folder_id = ? AND position > ?",
                (row["folder_id"], row["position"]),
            )

    def create_row(self, table_id: int, name: str) -> TableRow:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Row name cannot be empty")
        with self.database.connect() as conn:
            position = conn.execute(
                "SELECT COALESCE(MAX(position), 0) FROM table_rows WHERE table_id = ?", (table_id,)
            ).fetchone()[0]
            cursor = conn.execute(
                "INSERT INTO table_rows(table_id, name, position) VALUES(?, ?, ?)",
                (table_id, cleaned, position + 1),
            )
            return TableRow(cursor.lastrowid, table_id, cleaned, position + 1)

    def create_column(self, table_id: int, name: str) -> TableColumn:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Column name cannot be empty")
        with self.database.connect() as conn:
            position = conn.execute(
                "SELECT COALESCE(MAX(position), 0) FROM table_columns WHERE table_id = ?", (table_id,)
            ).fetchone()[0]
            cursor = conn.execute(
                "INSERT INTO table_columns(table_id, name, position) VALUES(?, ?, ?)",
                (table_id, cleaned, position + 1),
            )
            return TableColumn(cursor.lastrowid, table_id, cleaned, position + 1)

    def rename_row(self, row_id: int, name: str) -> None:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Row name cannot be empty")
        with self.database.connect() as conn:
            conn.execute("UPDATE table_rows SET name = ? WHERE id = ?", (cleaned, row_id))

    def rename_column(self, column_id: int, name: str) -> None:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Column name cannot be empty")
        with self.database.connect() as conn:
            conn.execute("UPDATE table_columns SET name = ? WHERE id = ?", (cleaned, column_id))

    def delete_row(self, row_id: int) -> None:
        with self.database.connect() as conn:
            row = conn.execute("SELECT table_id, position FROM table_rows WHERE id = ?", (row_id,)).fetchone()
            if row is None:
                return
            conn.execute("DELETE FROM table_rows WHERE id = ?", (row_id,))
            conn.execute(
                "UPDATE table_rows SET position = position - 1 WHERE table_id = ? AND position > ?",
                (row["table_id"], row["position"]),
            )

    def delete_column(self, column_id: int) -> None:
        with self.database.connect() as conn:
            col = conn.execute(
                "SELECT table_id, position FROM table_columns WHERE id = ?", (column_id,)
            ).fetchone()
            if col is None:
                return
            conn.execute("DELETE FROM table_columns WHERE id = ?", (column_id,))
            conn.execute(
                "UPDATE table_columns SET position = position - 1 WHERE table_id = ? AND position > ?",
                (col["table_id"], col["position"]),
            )

    def reorder_rows(self, table_id: int, ordered_row_ids: list[int]) -> None:
        self._reorder_generic(
            table_id=table_id,
            ordered_ids=ordered_row_ids,
            table_name="table_rows",
            id_column="id",
        )

    def reorder_columns(self, table_id: int, ordered_column_ids: list[int]) -> None:
        self._reorder_generic(
            table_id=table_id,
            ordered_ids=ordered_column_ids,
            table_name="table_columns",
            id_column="id",
        )

    def _reorder_generic(self, table_id: int, ordered_ids: list[int], table_name: str, id_column: str) -> None:
        if not ordered_ids:
            return
        with self.database.connect() as conn:
            rows = conn.execute(
                f"SELECT {id_column} FROM {table_name} WHERE table_id = ? ORDER BY position, id",
                (table_id,),
            ).fetchall()
            existing_ids = [row[id_column] for row in rows]
            existing_set = set(existing_ids)
            reordered_ids = []
            seen = set()
            for item_id in ordered_ids:
                if item_id in existing_set and item_id not in seen:
                    reordered_ids.append(item_id)
                    seen.add(item_id)
            for item_id in existing_ids:
                if item_id not in seen:
                    reordered_ids.append(item_id)
            case_clauses = []
            parameters = []
            for position, item_id in enumerate(reordered_ids, start=1):
                case_clauses.append("WHEN ? THEN ?")
                parameters.extend([item_id, position])
            in_clause = ", ".join(["?"] * len(reordered_ids))
            parameters.extend([table_id, *reordered_ids])
            conn.execute(
                f"""
                UPDATE {table_name}
                SET position = CASE {id_column} {' '.join(case_clauses)} ELSE position END
                WHERE table_id = ? AND {id_column} IN ({in_clause})
                """,
                parameters,
            )

    def set_cell_completed(self, row_id: int, column_id: int, completed: bool) -> TableCell:
        value = 1 if completed else 0
        with self.database.connect() as conn:
            row_table = conn.execute(
                "SELECT table_id FROM table_rows WHERE id = ?", (row_id,)
            ).fetchone()
            col_table = conn.execute(
                "SELECT table_id FROM table_columns WHERE id = ?", (column_id,)
            ).fetchone()
            if row_table is None or col_table is None or row_table["table_id"] != col_table["table_id"]:
                raise ValueError("Row and column must exist and belong to the same table")
            conn.execute(
                """
                INSERT INTO table_cells(row_id, column_id, completed)
                VALUES(?, ?, ?)
                ON CONFLICT(row_id, column_id)
                DO UPDATE SET completed = excluded.completed
                """,
                (row_id, column_id, value),
            )
        return TableCell(row_id=row_id, column_id=column_id, completed=completed)

    def toggle_cell(self, row_id: int, column_id: int) -> TableCell:
        with self.database.connect() as conn:
            row = conn.execute(
                "SELECT completed FROM table_cells WHERE row_id = ? AND column_id = ?",
                (row_id, column_id),
            ).fetchone()
        current = bool(row["completed"]) if row else False
        return self.set_cell_completed(row_id, column_id, not current)
