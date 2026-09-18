import logging

from .table_service import TableService
from .todo_service import TodoService

logger = logging.getLogger(__name__)

try:
    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gdk, Gtk
except Exception:  # pragma: no cover
    Gtk = None
    Gdk = None


class TodoPanel:
    DEFAULT_WIDTH = 520

    def __init__(self, todo_service: TodoService, table_service: TableService):
        if Gtk is None:
            raise RuntimeError("GTK is unavailable")
        self.todo_service = todo_service
        self.table_service = table_service
        self.current_folder = None
        self.visible = True
        self.window = None
        self.table_view = "table"

        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.container.set_size_request(self.DEFAULT_WIDTH, -1)
        self.container.set_border_width(0)
        self.container.set_hexpand(False)
        self.container.set_can_focus(True)

        self.title = Gtk.Label(label="NEMO TODO")
        self.title.set_xalign(0)
        self.title.get_style_context().add_class("title")
        self.path_label = Gtk.Label(label="")
        self.path_label.set_xalign(0)
        self.path_label.set_ellipsize(3)
        self.path_label.get_style_context().add_class("dim-label")

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        header.set_border_width(14)
        header.get_style_context().add_class("header")
        header.pack_start(self.title, False, False, 0)
        header.pack_start(self.path_label, False, False, 0)

        self.actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.actions.set_margin_top(8)
        new_task_button = Gtk.Button.new_with_label("New TODO")
        new_task_button.set_tooltip_text("Create a TODO in this folder")
        new_task_button.connect("clicked", self._prompt_create_task)
        new_table_button = Gtk.Button.new_with_label("New table")
        new_table_button.set_tooltip_text("Create a checklist table in this folder")
        new_table_button.connect("clicked", self._prompt_create_table)
        self.actions.pack_start(new_task_button, False, False, 0)
        self.actions.pack_start(new_table_button, False, False, 0)
        header.pack_start(self.actions, False, False, 0)

        self.task_list = Gtk.ListBox()
        self.task_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.task_list.set_placeholder(self._empty_label("No TODOs in this folder"))
        self.task_list.get_style_context().add_class("task-list")

        self.tables_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.tables_box.set_border_width(12)

        self.table_mode = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.table_mode.set_halign(Gtk.Align.END)
        self.table_mode.get_style_context().add_class("linked")
        self.table_button = Gtk.ToggleButton.new_with_label("Table")
        self.card_button = Gtk.ToggleButton.new_with_label("Cards")
        self.table_button.set_active(True)
        self.table_button.connect("toggled", self._on_table_mode_toggled)
        self.card_button.connect("toggled", self._on_card_mode_toggled)
        self.table_mode.pack_start(self.table_button, False, False, 0)
        self.table_mode.pack_start(self.card_button, False, False, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.set_border_width(0)
        content.pack_start(self._section_header("TODOs", None), False, False, 0)
        task_scroll = Gtk.ScrolledWindow()
        task_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        task_scroll.set_min_content_height(110)
        task_scroll.add(self.task_list)
        content.pack_start(task_scroll, False, True, 0)

        checklist_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        checklist_header.set_border_width(12)
        checklist_header.get_style_context().add_class("section-header")
        checklist_header.pack_start(Gtk.Label(label="CHECKLISTS", xalign=0), True, True, 0)
        checklist_header.pack_start(self.table_mode, False, False, 0)
        content.pack_start(checklist_header, False, False, 0)

        table_scroll = Gtk.ScrolledWindow()
        table_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        table_scroll.add(self.tables_box)
        content.pack_start(table_scroll, True, True, 0)

        self.container.pack_start(header, False, False, 0)
        self.container.pack_start(content, True, True, 0)

        self._install_css()

        self.container.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.container.connect("key-press-event", self._on_key_press)

    def widget(self):
        return self.container

    def set_window(self, window):
        self.window = window

    def show(self):
        self.visible = True
        self.container.set_visible(True)
        window = getattr(self, "window", None)
        if window is not None:
            window.show_all()

    def hide(self):
        self.visible = False
        self.container.set_visible(False)
        window = getattr(self, "window", None)
        if window is not None:
            window.hide()

    def set_folder(self, folder_path: str):
        if folder_path == self.current_folder:
            return
        self.current_folder = folder_path
        self.path_label.set_text(folder_path)
        self.reload()

    def _install_css(self):
        css = Gtk.CssProvider()
        css.load_from_data(
            b"""
            .header { background: @theme_base_color; border-bottom: 1px solid @borders; }
            .title { font-weight: bold; font-size: 1.2em; }
            .section-header { background: @theme_bg_color; border-bottom: 1px solid @borders; }
            .task-list row { padding: 5px 10px; border-bottom: 1px solid @borders; }
            .table-card { margin: 0 0 8px; padding: 8px; border: 1px solid @borders; border-radius: 5px; }
            .table-title { font-weight: bold; }
            .table-meta { color: @insensitive_fg_color; }
            """
        )
        screen = self.container.get_screen() or Gdk.Screen.get_default()
        if screen is not None:
            Gtk.StyleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _empty_label(self, text):
        label = Gtk.Label(label=text)
        label.set_xalign(0)
        label.set_margin_start(12)
        label.set_margin_end(12)
        label.set_margin_top(14)
        label.set_margin_bottom(14)
        label.get_style_context().add_class("dim-label")
        return label

    def _section_header(self, title, action):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.set_border_width(12)
        header.get_style_context().add_class("section-header")
        header.pack_start(Gtk.Label(label=title, xalign=0), True, True, 0)
        if action is not None:
            header.pack_end(action, False, False, 0)
        return header

    def reload(self):
        if not self.current_folder:
            return
        self._rebuild_tasks()
        self._rebuild_tables()

    def toggle_visible(self):
        self.visible = not self.visible
        self.container.set_visible(self.visible)
        window = getattr(self, "window", None)
        if window is not None:
            if self.visible:
                window.show_all()
            else:
                window.hide()

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

    def _prompt_for_name(self, title: str, placeholder: str):
        dialog = Gtk.Dialog(title=title, transient_for=self.window, modal=True)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Create", Gtk.ResponseType.OK)
        entry = Gtk.Entry()
        entry.set_placeholder_text(placeholder)
        entry.set_activates_default(True)
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.get_content_area().pack_start(entry, False, False, 12)
        dialog.show_all()
        response = dialog.run()
        text = entry.get_text().strip()
        dialog.destroy()
        return text if response == Gtk.ResponseType.OK and text else None

    def _prompt_create_task(self, _button):
        text = self._prompt_for_name("New TODO", "TODO text")
        if text:
            self._create_task(text)

    def _prompt_create_table(self, _button):
        text = self._prompt_for_name("New checklist table", "Table name")
        if text:
            self._create_table(text)

    def _create_task(self, text: str):
        if not self.current_folder:
            return
        self.todo_service.create_task(self.current_folder, text)
        self._rebuild_tasks()

    def _create_table(self, text: str):
        if not self.current_folder:
            return
        self.table_service.create_table(self.current_folder, text)
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

            delete_button = self._icon_button("user-trash-symbolic", "Delete TODO")
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

    def _icon_button(self, icon_name, tooltip):
        button = Gtk.Button()
        button.add(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON))
        button.set_tooltip_text(tooltip)
        button.set_relief(Gtk.ReliefStyle.NONE)
        return button

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

    def _on_table_mode_toggled(self, button):
        if not button.get_active():
            return
        self.card_button.set_active(False)
        self.table_view = "table"
        self._rebuild_tables()

    def _on_card_mode_toggled(self, button):
        if not button.get_active():
            return
        self.table_button.set_active(False)
        self.table_view = "cards"
        self._rebuild_tables()

    def _rebuild_tables(self):
        self._clear_box(self.tables_box)
        snapshots = self.table_service.list_tables(self.current_folder)
        if not snapshots:
            self.tables_box.pack_start(self._empty_label("No checklists in this folder"), False, False, 0)
        for snapshot in snapshots:
            frame = Gtk.Frame()
            frame.get_style_context().add_class("table-card")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

            table_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            table_name = Gtk.Entry()
            table_name.set_text(snapshot.table.name)
            table_name.get_style_context().add_class("table-title")
            table_name.set_tooltip_text("Rename table")
            table_name.connect("activate", self._rename_table, snapshot.table.id)
            delete_table = self._icon_button("user-trash-symbolic", "Delete table")
            delete_table.connect("clicked", self._delete_table, snapshot.table.id)
            table_actions.pack_start(table_name, True, True, 0)
            table_actions.pack_start(delete_table, False, False, 0)
            vbox.pack_start(table_actions, False, False, 0)

            completed = sum(snapshot.cells.get((row.id, column.id), False) for row in snapshot.rows for column in snapshot.columns)
            total = len(snapshot.rows) * len(snapshot.columns)
            summary = Gtk.Label(label=f"{completed}/{total} completed" if total else "No cells yet", xalign=0)
            summary.get_style_context().add_class("table-meta")
            vbox.pack_start(summary, False, False, 0)

            if self.table_view == "cards":
                vbox.pack_start(self._build_card_view(snapshot), False, False, 0)
            else:
                table_scroll = Gtk.ScrolledWindow()
                table_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
                table_scroll.add(self._build_table_view(snapshot))
                vbox.pack_start(table_scroll, False, False, 0)

            add_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            add_row = Gtk.Button.new_with_label("Add row")
            add_row.connect("clicked", self._prompt_add_row, snapshot.table.id)
            add_column = Gtk.Button.new_with_label("Add column")
            add_column.connect("clicked", self._prompt_add_column, snapshot.table.id)
            add_actions.pack_start(add_row, False, False, 0)
            add_actions.pack_start(add_column, False, False, 0)
            vbox.pack_start(add_actions, False, False, 0)

            frame.add(vbox)
            self.tables_box.pack_start(frame, False, False, 0)
        self.tables_box.show_all()

    def _build_table_view(self, snapshot):
        grid = Gtk.Grid(column_spacing=4, row_spacing=2)
        grid.set_column_spacing(4)
        grid.set_row_spacing(2)
        row_header = Gtk.Label(label="Item", xalign=0)
        row_header.set_size_request(150, -1)
        grid.attach(row_header, 0, 0, 1, 1)
        for column_index, column in enumerate(snapshot.columns, start=1):
            column_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            column_name = Gtk.Entry()
            column_name.set_text(column.name)
            column_name.set_width_chars(8)
            column_name.set_tooltip_text("Rename column")
            column_name.connect("activate", self._rename_column, column.id)
            delete_column = self._icon_button("user-trash-symbolic", "Delete column")
            delete_column.connect("clicked", self._delete_column, column.id)
            column_box.pack_start(column_name, True, True, 0)
            column_box.pack_start(delete_column, False, False, 0)
            column_box.set_size_request(100, -1)
            grid.attach(column_box, column_index, 0, 1, 1)
        for row_index, row in enumerate(snapshot.rows, start=1):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            row_name = Gtk.Entry()
            row_name.set_text(row.name)
            row_name.set_tooltip_text("Rename row")
            row_name.connect("activate", self._rename_row, row.id)
            row_name.set_width_chars(12)
            delete_row = self._icon_button("user-trash-symbolic", "Delete row")
            delete_row.connect("clicked", self._delete_row, row.id)
            row_box.pack_start(row_name, True, True, 0)
            row_box.pack_start(delete_row, False, False, 0)
            row_box.set_size_request(150, -1)
            grid.attach(row_box, 0, row_index, 1, 1)
            for column_index, column in enumerate(snapshot.columns, start=1):
                grid.attach(self._cell_checkbox(snapshot, row, column), column_index, row_index, 1, 1)
        return grid

    def _build_card_view(self, snapshot):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for row in snapshot.rows:
            row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            row_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            row_name = Gtk.Entry()
            row_name.set_text(row.name)
            row_name.set_tooltip_text("Rename row")
            row_name.connect("activate", self._rename_row, row.id)
            delete_row = self._icon_button("user-trash-symbolic", "Delete row")
            delete_row.connect("clicked", self._delete_row, row.id)
            row_header.pack_start(row_name, True, True, 0)
            row_header.pack_start(delete_row, False, False, 0)
            row_box.pack_start(row_header, False, False, 0)
            box.pack_start(row_box, False, False, 0)
            for column in snapshot.columns:
                cell_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                cell_row.pack_start(self._cell_checkbox(snapshot, row, column), False, False, 0)
                cell_row.pack_start(Gtk.Label(label=column.name, xalign=0), True, True, 0)
                cell_row.set_margin_start(8)
                box.pack_start(cell_row, False, False, 0)
        return box

    def _cell_checkbox(self, snapshot, row, column):
        checked = snapshot.cells.get((row.id, column.id), False)
        cell = Gtk.CheckButton()
        cell.set_active(checked)
        cell_description = f"{row.name} / {column.name}"
        cell.set_tooltip_text(cell_description)
        if cell.get_accessible():
            cell.get_accessible().set_name(cell_description)
        cell.connect("toggled", self._toggle_cell, row.id, column.id)
        return cell

    def _prompt_add_row(self, _button, table_id):
        text = self._prompt_for_name("Add row", "Row name")
        if text:
            self._add_row(table_id, text)

    def _prompt_add_column(self, _button, table_id):
        text = self._prompt_for_name("Add column", "Column name")
        if text:
            self._add_column(table_id, text)

    def _add_row(self, table_id, text):
        self.table_service.create_row(table_id, text)
        self.reload()

    def _add_column(self, table_id, text):
        self.table_service.create_column(table_id, text)
        self.reload()

    def _rename_table(self, entry, table_id):
        try:
            self.table_service.rename_table(table_id, entry.get_text())
        except ValueError:
            logger.warning("Table name cannot be empty")
        self._rebuild_tables()

    def _delete_table(self, _button, table_id):
        self.table_service.delete_table(table_id)
        self._rebuild_tables()

    def _rename_row(self, entry, row_id):
        try:
            self.table_service.rename_row(row_id, entry.get_text())
        except ValueError:
            logger.warning("Row name cannot be empty")
        self._rebuild_tables()

    def _delete_row(self, _button, row_id):
        self.table_service.delete_row(row_id)
        self._rebuild_tables()

    def _rename_column(self, entry, column_id):
        try:
            self.table_service.rename_column(column_id, entry.get_text())
        except ValueError:
            logger.warning("Column name cannot be empty")
        self._rebuild_tables()

    def _delete_column(self, _button, column_id):
        self.table_service.delete_column(column_id)
        self._rebuild_tables()

    def _toggle_cell(self, checkbox, row_id, column_id):
        self.table_service.set_cell_completed(row_id, column_id, checkbox.get_active())
