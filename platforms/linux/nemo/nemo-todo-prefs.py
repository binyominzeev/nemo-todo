#!/usr/bin/python3

import signal

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("XApp", "1.0")
from gi.repository import Gdk, Gio, Gtk, XApp


SCHEMA_ID = "org.nemo.extensions.nemo-todo"


class LabeledItem(Gtk.Box):
    def __init__(self, label, item):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.label_widget = Gtk.Label(label=label, xalign=0)
        self.pack_start(self.label_widget, True, True, 6)
        self.pack_end(item, False, False, 6)
        self.show_all()


class Page(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.set_margin_start(15)
        self.set_margin_end(15)
        self.set_margin_top(15)
        self.set_margin_bottom(15)


class NemoTodoPreferencesWindow(XApp.PreferencesWindow):
    def __init__(self):
        super().__init__()
        self.set_icon_name("checkbox-checked-symbolic")
        self.set_title("Nemo TODO Preferences")
        self.set_skip_taskbar_hint(False)
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.connect("destroy", Gtk.main_quit)

        self.settings = Gio.Settings.new(SCHEMA_ID)
        frame = Gtk.Frame()
        frame.get_style_context().add_class("view")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame.add(box)
        store = Gtk.ListStore(int, Gdk.ModifierType)
        treeview = Gtk.TreeView(model=store, headers_visible=False, enable_search=False)
        cell = Gtk.CellRendererAccel(editable=True, accel_mode=Gtk.CellRendererAccelMode.GTK, width=140)
        column = Gtk.TreeViewColumn("binding", cell, accel_key=0, accel_mods=1)
        treeview.append_column(column)

        def update_accel_from_settings(settings, _pspec=None):
            keyval, modifiers = Gtk.accelerator_parse(settings.get_string("panel-hotkey"))
            store.clear()
            if keyval:
                store.append((keyval, modifiers))

        def on_accel_changed(_accel, _path, key, modifiers, _hardware_keycode):
            self.settings.set_string("panel-hotkey", Gtk.accelerator_name(key, modifiers))

        def on_accel_cleared(_accel, _path):
            self.settings.set_string("panel-hotkey", "")

        self.settings.connect("changed::panel-hotkey", update_accel_from_settings)
        cell.connect("accel-edited", on_accel_changed)
        cell.connect("accel-cleared", on_accel_cleared)
        update_accel_from_settings(self.settings)
        box.pack_start(treeview, False, False, 6)

        shortcut_item = LabeledItem("Keyboard shortcut", frame)
        page = Page()
        page.pack_start(shortcut_item, False, False, 0)

        reset_button = Gtk.Button(label="Restore default")
        reset_button.connect("clicked", lambda _button: self.settings.reset("panel-hotkey"))
        page.pack_start(reset_button, False, False, 0)
        self.add_page(page, "main", "Basic")
        self.show_all()
        self.present()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    NemoTodoPreferencesWindow()
    Gtk.main()
