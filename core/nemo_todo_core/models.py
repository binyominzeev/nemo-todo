from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class Task:
    id: int
    folder_id: int
    text: str
    completed: bool
    position: int
    created_at: str


@dataclass(frozen=True)
class ChecklistTable:
    id: int
    folder_id: int
    name: str
    position: int


@dataclass(frozen=True)
class TableColumn:
    id: int
    table_id: int
    name: str
    position: int
    type: str = "checkbox"


@dataclass(frozen=True)
class TableRow:
    id: int
    table_id: int
    name: str
    position: int


@dataclass(frozen=True)
class TableCell:
    row_id: int
    column_id: int
    completed: bool
    text_value: str | None = None


@dataclass(frozen=True)
class TableSnapshot:
    table: ChecklistTable
    rows: List[TableRow]
    columns: List[TableColumn]
    cells: Dict[tuple[int, int], bool]
    text_values: Dict[tuple[int, int], str] = field(default_factory=dict)
