import copy
import json
import numpy as np
import os
import pathlib
import time

from collections import deque
from datetime import datetime, timezone

from .._gtk4 import GLib, Gtk, Pango, Gio

from ...import slipp, utils

class CommandBox(Gtk.Box):
    """
    A Command box for sending arbitrary command to the spider.
    """
    def __init__(self, main_utils):
        """
        main_utils : Class with shared utilities from the MainWindow.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.set_margin_top(5)

        self.main_utils = main_utils
        self.refresh_rate_ms = 250

        # Columns boxes
        self.column_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.append(self.column_box)
        self.left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.left_col.set_margin_start(5)
        self.middle_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.right_col.set_margin_end(5)
        self.column_box.append(self.left_col)
        self.column_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self.column_box.append(self.middle_col)
        self.column_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self.column_box.append(self.right_col)

        # Left columns, send button and status prints
        self.send_btn = Gtk.Button(label="Send Command")
        self.send_btn.connect("clicked", self.on_send_command)
        self.send_btn.set_size_request(-1, 50)
        self.left_col.append(self.send_btn)
        self.status_scroll = Gtk.ScrolledWindow()
        self.status_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.status_scroll.set_vexpand(True)
        self.status_scroll.set_hexpand(True)
        self.left_col.append(self.status_scroll)

        self.status_textbuffer = Gtk.TextBuffer()
        self.status_textbuffer.set_text("")

        self.stats_textview = Gtk.TextView(buffer=self.status_textbuffer)
        self.stats_textview.set_editable(False)
        self.stats_textview.set_cursor_visible(False)
        self.stats_textview.set_monospace(True)
        self.status_scroll.set_child(self.stats_textview)

        self.status_textbuffer_maxlen = 2**16
        self.status_tag = self.status_textbuffer.create_tag("common",
            size=10 * Pango.SCALE,
            weight=Pango.Weight.BOLD,
        )

        # Middle column: Enter command arguments
        self.arglist_title = Gtk.Label(label="Arguments")
        self.arglist_title.set_size_request(200, 30)
        self.middle_col.append(self.arglist_title)
        self.arglist_args = []

        # Right column, list and refresh commands
        # Note, this is quite complicated, for some reason...
        self.cmdlist_order = []
        self.cmdlist_lookup = dict()
        self.cmdlist_title = Gtk.Label(label="Commands")
        self.cmdlist_refresh_btn = Gtk.Button(label="Refresh List")
        self.cmdlist_refresh_btn.set_size_request(200, 30)
        self.cmdlist_refresh_btn.connect("clicked", self.on_refresh_cmdlist)
        self.cmdlist_scroll = Gtk.ScrolledWindow()
        self.cmdlist_scroll.set_vexpand(True)
        self.cmdlist_scroll.set_has_frame(True)
        self.cmdlist_store = Gio.ListStore()
        self.cmdlist_model = Gtk.SingleSelection(model=self.cmdlist_store)
        self.cmdlist_model.connect("selection-changed", self.on_select_cmdlist)
        self.cmdlist_factory = Gtk.SignalListItemFactory()

        def f_bind(factory, listitem):
            listitem.set_child(listitem.get_item())
        def f_unbind(factory, listitem):
            listitem.set_child(None)

        self.cmdlist_factory.connect("bind", f_bind)
        self.cmdlist_factory.connect("unbind", f_unbind)
        self.cmdlist_view = Gtk.ListView(model=self.cmdlist_model, factory=self.cmdlist_factory)
        self.cmdlist_scroll.set_child(self.cmdlist_view)
        self.right_col.append(self.cmdlist_title)
        self.right_col.append(self.cmdlist_refresh_btn)
        self.right_col.append(self.cmdlist_scroll)

    def set_nargs_visible(self, n):
        if len(self.arglist_args) < n:
            for i in range(len(self.arglist_args), n):
                arg = Gtk.Entry()
                arg.set_text("")
                arg.set_placeholder_text(f"Arg {i + 1}")
                self.arglist_args.append(arg)
                self.middle_col.append(arg)

        for i, arg in enumerate(self.arglist_args):
            is_active = bool(i < n)
            arg.set_editable(is_active)
            arg.set_can_target(is_active)
            arg.set_visible(is_active)

    def append_to_textbuffer(self, txt):
        self.status_textbuffer.insert_with_tags(
            self.status_textbuffer.get_start_iter(),
            txt,
            self.status_tag
        )
        self.refresh()

    def on_refresh_cmdlist(self, btn):
        """Refreshing the available list of commands."""
        def on_packet_callback(pkt):
            commands = pkt.contents["commands"]
            self.cmdlist_order = list(commands.keys())
            for cmd, info in commands.items():
                if cmd not in self.cmdlist_lookup:
                    label = Gtk.Label(label=cmd)
                    label.set_size_request(-1, 30)
                    self.cmdlist_lookup[cmd] = {"label": label}
                self.cmdlist_lookup[cmd]["argtypes"] = info["argtypes"]
                self.cmdlist_lookup[cmd]["kind"] = info["kind"]

            self.cmdlist_store.remove_all()
            for cmd in self.cmdlist_order:
                self.cmdlist_store.append(self.cmdlist_lookup[cmd])

            self.cmdlist_model.set_selected(0)

        def on_timeout_callback():
            self.main_utils.notify("Command list refresh timed out")

        self.main_utils.client_send(slipp.Packet("LSCMD"),
            on_recv_callback=on_packet_callback,
            on_timeout_callback=on_timeout_callback,
        )

        #i = self.cmdlist_model.get_selected()
        #print(f"Selected: {i}")
        #self.cmdlist_store.remove(i)
        #self.cmdlist_store.remove_all()
        #TEST_LIST = ["apple", "banana", "carrot", "durian", "edamer", "fromage", "grape", "halloumi"]
        #np.random.shuffle(TEST_LIST)
        #for tl in TEST_LIST:
        #    label = Gtk.Label(label=tl)
        #    label.set_size_request(-1, 30)
        #    self.cmdlist_store.append(label)

    def on_select_cmdlist(self, model, pos, n_items):
        # model, pos, n_items can be ignored... pos and n_items seems to have strange behavior.
        i = self.cmdlist_model.get_selected()
        cmd = self.cmdlist_order[i]
        n_args = len(self.cmdlist_lookup[cmd]["argtypes"])
        self.set_nargs_visible(n_args)

    def on_send_command(self, btn):
        """Send the selected command."""
        i = self.cmdlist_model.get_selected()
        if i not in range(len(self.cmdlist_order)):
            self.main_utils.notify("Cannot send command, no command selected")
            return

        cmd = self.cmdlist_order[i]
        at_lookup = {
            "int": int,
            "str": str,
        }

        args = []
        failed = False
        for i, at in enumerate(self.cmdlist_lookup[cmd]["argtypes"]):
            try:
                argentry = self.arglist_args[i]
                arg = at_lookup[at](argentry.get_text())
                args.append(arg)
            except Exception as e:
                failed = True
                self.main_utils.notify(f"Error on command argument {i+1}: {str(e)}")

        if failed:
            return

        def on_packet_callback(pkt):
            # Successfully got a packet
            recv_txt = "\n".join([
                "----------------------------------",
                "------- RECEIVED RESPONSE: -------",
                json.dumps(pkt.blob, indent=4),
            ])
            self.append_to_textbuffer(recv_txt)

        def on_timeout_callback():
            # Packet timedout
            self.main_utils.notify("Command timed out")

        out_pkt = slipp.Packet(cmd, contents={"args": args})

        self.main_utils.client_send(out_pkt,
            on_recv_callback=on_packet_callback,
            on_timeout_callback=on_timeout_callback,
        )

        send_txt = "\n".join([
            "---------------------------------",
            "--------- SENT COMMAND: ---------",
            json.dumps(out_pkt.blob, indent=4),
        ])
        self.append_to_textbuffer(send_txt)

    def refresh(self):
        if self.status_textbuffer.get_char_count() > self.status_textbuffer_maxlen:
            # Remove too old text
            start_iter = self.status_textbuffer.get_iter_at_offset(int(self.status_textbuffer_maxlen * 0.9))
            end_iter = self.status_textbuffer.get_end_iter()
            self.status_textbuffer.delete(start_iter, end_iter)
