import logging

from .table_service import TableService
from .todo_service import TodoService

logger = logging.getLogger(__name__)

try:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gdk, Gtk
except Exception:  # pragma: no cover
    Gtk = None
    Gdk = None


class TodoPanel:
    DEFAULT_WIDTH = 300

    def __init__(self, todo_service: TodoService, table_service: TableService):
        if Gtk is None:
            raise RuntimeError("GTK is unavailable")
        self.todo_service = todo_service
        self.table_service = table_service
        self.current_folder = None
        self.visible = True

        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.container.set_size_request(self.DEFAULT_WIDTH, -1)
        self.container.set_border_width(6)
        self.container.set_hexpand(False)
        self.container.set_can_focus(True)

        self.title = Gtk.Label(label="TODO")
        self.title.set_xalign(0)
        self.path_label = Gtk.Label(label="")
        self.path_label.set_xalign(0)

        self.task_list = Gtk.ListBox()
        self.task_list.set_selection_mode(Gtk.SelectionMode.NONE)

        self.new_task_entry = Gtk.Entry()
        self.new_task_entry.set_placeholder_text("+ New TODO")
        self.new_task_entry.connect("activate", self._create_task)

        self.tables_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.new_table_entry = Gtk.Entry()
        self.new_table_entry.set_placeholder_text("+ New table")
        self.new_table_entry.connect("activate", self._create_table)

        self.container.pack_start(self.title, False, False, 0)
        self.container.pack_start(self.path_label, False, False, 0)
        self.container.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
        self.container.pack_start(self.task_list, True, True, 0)
        self.container.pack_start(self.new_task_entry, False, False, 0)
        self.container.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
        self.container.pack_start(Gtk.Label(label="CHECKLIST TABLES", xalign=0), False, False, 0)
        self.container.pack_start(self.tables_box, True, True, 0)
        self.container.pack_start(self.new_table_entry, False, False, 0)

        self.container.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.container.connect("key-press-event", self._on_key_press)

    def widget(self):
        return self.container

    def set_folder(self, folder_path: str):
        if folder_path == self.current_folder:
            return
        self.current_folder = folder_path
        self.path_label.set_text(folder_path)
        self.reload()

    def reload(self):
        if not self.current_folder:
            return
        self._rebuild_tasks()
        self._rebuild_tables()

    def toggle_visible(self):
        self.visible = not self.visible
        self.container.set_visible(self.visible)

    def _on_key_press(self, _widget, event):
        if event.keyval in (Gdk.KEY_t, Gdk.KEY_T) and (event.state & Gdk.ModifierType.CONTROL_MASK) and (
            event.state & Gdk.ModifierType.MOD1_MASK
        ):
            self.toggle_visible()
            return True
        return False

    def _clear_box(self, box):
        if isinstance(box, Gtk.ListBox):
            row = box.get_row_at_index(0)
            while row is not None:
                box.remove(row)
                row = box.get_row_at_index(0)
            return
        for child in box.get_children():
            box.remove(child)

    def _create_task(self, _entry):
        if not self.current_folder:
            return
        text = self.new_task_entry.get_text()
        if not text.strip():
            return
        self.todo_service.create_task(self.current_folder, text)
        self.new_task_entry.set_text("")
        self._rebuild_tasks()

    def _create_table(self, _entry):
        if not self.current_folder:
            return
        text = self.new_table_entry.get_text()
        if not text.strip():
            return
        self.table_service.create_table(self.current_folder, text)
        self.new_table_entry.set_text("")
        self._rebuild_tables()

    def _rebuild_tasks(self):
        self._clear_box(self.task_list)
        tasks = self.todo_service.list_tasks(self.current_folder)
        for task in tasks:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            checkbox = Gtk.CheckButton()
            checkbox.set_active(task.completed)
            checkbox.connect("toggled", self._toggle_task, task.id)

            entry = Gtk.Entry()
            entry.set_text(task.text)
            entry.connect("activate", self._rename_task, task.id)

            delete_button = Gtk.Button.new_with_label("Delete")
            delete_button.set_tooltip_text("Delete TODO")
            if delete_button.get_accessible():
                delete_button.get_accessible().set_name("Delete TODO")
            delete_button.connect("clicked", self._delete_task, task.id)

            row.pack_start(checkbox, False, False, 0)
            row.pack_start(entry, True, True, 0)
            row.pack_start(delete_button, False, False, 0)

            list_row = Gtk.ListBoxRow()
            list_row.add(row)
            self.task_list.add(list_row)

        self.task_list.show_all()

    def _toggle_task(self, checkbox, task_id: int):
        self.todo_service.set_task_completed(task_id, checkbox.get_active())

    def _rename_task(self, entry, task_id: int):
        try:
            self.todo_service.update_task_text(task_id, entry.get_text())
        except ValueError:
            logger.warning("Task text cannot be empty")
            self._rebuild_tasks()

    def _delete_task(self, _button, task_id: int):
        self.todo_service.delete_task(task_id)
        self._rebuild_tasks()

    def _rebuild_tables(self):
        self._clear_box(self.tables_box)
        snapshots = self.table_service.list_tables(self.current_folder)
        for snapshot in snapshots:
            frame = Gtk.Frame(label=snapshot.table.name)
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

            header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            header_row.pack_start(Gtk.Label(label=" ", xalign=0), True, True, 0)
            for column in snapshot.columns:
                header_row.pack_start(Gtk.Label(label=column.name, xalign=0), True, True, 0)
            vbox.pack_start(header_row, False, False, 0)

            for row in snapshot.rows:
                data_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                data_row.pack_start(Gtk.Label(label=row.name, xalign=0), True, True, 0)
                for column in snapshot.columns:
                    checked = snapshot.cells.get((row.id, column.id), False)
                    cell = Gtk.CheckButton()
                    cell.set_active(checked)
                    cell_description = f"{row.name} / {column.name}"
                    cell.set_tooltip_text(cell_description)
                    if cell.get_accessible():
                        cell.get_accessible().set_name(cell_description)
                    cell.connect("toggled", self._toggle_cell, row.id, column.id)
                    data_row.pack_start(cell, True, True, 0)
                vbox.pack_start(data_row, False, False, 0)

            add_row = Gtk.Entry()
            add_row.set_placeholder_text("+ Row")
            add_row.connect("activate", self._add_row, snapshot.table.id)
            vbox.pack_start(add_row, False, False, 0)

            add_col = Gtk.Entry()
            add_col.set_placeholder_text("+ Column")
            add_col.connect("activate", self._add_column, snapshot.table.id)
            vbox.pack_start(add_col, False, False, 0)

            frame.add(vbox)
            self.tables_box.pack_start(frame, False, False, 0)
        self.tables_box.show_all()

    def _add_row(self, entry, table_id):
        text = entry.get_text()
        if not text.strip():
            return
        self.table_service.create_row(table_id, text)
        entry.set_text("")
        self.reload()

    def _add_column(self, entry, table_id):
        text = entry.get_text()
        if not text.strip():
            return
        self.table_service.create_column(table_id, text)
        entry.set_text("")
        self.reload()

    def _toggle_cell(self, checkbox, row_id, column_id):
        self.table_service.set_cell_completed(row_id, column_id, checkbox.get_active())
