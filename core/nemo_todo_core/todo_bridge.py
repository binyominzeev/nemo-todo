import copy

from .table_service import TableService
from .todo_service import TodoService


class TodoBridgeError(ValueError):
    pass


class TodoBridge:
    """UI-independent command adapter for the local web frontend."""

    def __init__(self, todo_service: TodoService, table_service: TableService):
        self.todo_service = todo_service
        self.table_service = table_service
        self.current_folder = None

    def set_folder(self, folder: str):
        if not folder:
            raise TodoBridgeError("Folder is required")
        self.current_folder = folder

    def get_state(self) -> dict:
        folder = self._require_folder()
        tasks = self.todo_service.list_tasks(folder)
        tables = self.table_service.list_tables(folder)
        return {
            "folder": folder,
            "tasks": [
                {
                    "id": task.id,
                    "text": task.text,
                    "completed": task.completed,
                    "position": task.position,
                }
                for task in tasks
            ],
            "tables": [self._serialize_table(snapshot) for snapshot in tables],
        }

    def execute(self, command: str, payload: dict | None = None) -> dict:
        payload = copy.deepcopy(payload or {})
        handlers = {
            "get_state": self._get_state,
            "create_task": self._create_task,
            "update_task": self._update_task,
            "delete_task": self._delete_task,
            "toggle_task": self._toggle_task,
            "create_table": self._create_table,
            "rename_table": self._rename_table,
            "delete_table": self._delete_table,
            "create_row": self._create_row,
            "rename_row": self._rename_row,
            "delete_row": self._delete_row,
            "create_column": self._create_column,
            "rename_column": self._rename_column,
            "delete_column": self._delete_column,
            "update_column_type": self._update_column_type,
            "toggle_cell": self._toggle_cell,
            "set_cell_text": self._set_cell_text,
        }
        handler = handlers.get(command)
        if handler is None:
            raise TodoBridgeError(f"Unknown command: {command}")
        handler(payload)
        return self.get_state()

    def _require_folder(self):
        if not self.current_folder:
            raise TodoBridgeError("No folder selected")
        return self.current_folder

    def _required_int(self, payload, key):
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise TodoBridgeError(f"{key} must be an integer")
        return value

    def _required_text(self, payload, key):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise TodoBridgeError(f"{key} must be a non-empty string")
        return value

    def _get_state(self, _payload):
        return None

    def _create_task(self, payload):
        self.todo_service.create_task(self._require_folder(), self._required_text(payload, "text"))

    def _update_task(self, payload):
        self.todo_service.update_task_text(self._required_int(payload, "task_id"), self._required_text(payload, "text"))

    def _delete_task(self, payload):
        self.todo_service.delete_task(self._required_int(payload, "task_id"))

    def _toggle_task(self, payload):
        completed = payload.get("completed")
        if not isinstance(completed, bool):
            raise TodoBridgeError("completed must be a boolean")
        self.todo_service.set_task_completed(self._required_int(payload, "task_id"), completed)

    def _create_table(self, payload):
        self.table_service.create_table(self._require_folder(), self._required_text(payload, "name"))

    def _rename_table(self, payload):
        self.table_service.rename_table(self._required_int(payload, "table_id"), self._required_text(payload, "name"))

    def _delete_table(self, payload):
        self.table_service.delete_table(self._required_int(payload, "table_id"))

    def _create_row(self, payload):
        self.table_service.create_row(self._required_int(payload, "table_id"), self._required_text(payload, "name"))

    def _rename_row(self, payload):
        self.table_service.rename_row(self._required_int(payload, "row_id"), self._required_text(payload, "name"))

    def _delete_row(self, payload):
        self.table_service.delete_row(self._required_int(payload, "row_id"))

    def _create_column(self, payload):
        column_type = payload.get("type", "checkbox")
        self.table_service.create_column(self._required_int(payload, "table_id"), self._required_text(payload, "name"), column_type)

    def _rename_column(self, payload):
        self.table_service.rename_column(self._required_int(payload, "column_id"), self._required_text(payload, "name"))

    def _delete_column(self, payload):
        self.table_service.delete_column(self._required_int(payload, "column_id"))

    def _update_column_type(self, payload):
        self.table_service.update_column_type(self._required_int(payload, "column_id"), self._required_text(payload, "type"))

    def _toggle_cell(self, payload):
        completed = payload.get("completed")
        if not isinstance(completed, bool):
            raise TodoBridgeError("completed must be a boolean")
        self.table_service.set_cell_completed(
            self._required_int(payload, "row_id"), self._required_int(payload, "column_id"), completed
        )

    def _set_cell_text(self, payload):
        text = payload.get("text")
        if not isinstance(text, str):
            raise TodoBridgeError("text must be a string")
        self.table_service.set_cell_text(
            self._required_int(payload, "row_id"), self._required_int(payload, "column_id"), text
        )

    @staticmethod
    def _serialize_table(snapshot):
        cell_keys = set(snapshot.cells) | set(snapshot.text_values)
        return {
            "id": snapshot.table.id,
            "name": snapshot.table.name,
            "position": snapshot.table.position,
            "rows": [
                {"id": row.id, "name": row.name, "position": row.position}
                for row in snapshot.rows
            ],
            "columns": [
                {"id": column.id, "name": column.name, "position": column.position, "type": column.type}
                for column in snapshot.columns
            ],
            "cells": [
                {
                    "row_id": row_id,
                    "column_id": column_id,
                    "completed": snapshot.cells.get((row_id, column_id), False),
                    "text_value": snapshot.text_values.get((row_id, column_id), ""),
                }
                for (row_id, column_id) in cell_keys
            ],
        }
