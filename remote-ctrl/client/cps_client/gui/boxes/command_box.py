import copy

from collections import deque

from .._gtk4 import GLib, Gtk, Gdk

from ...import slipp

class CommandBox(Gtk.Box):
    """
    A Command box for sending motion commands to the spider.
    """
    def __init__(self, logfn, client_send):
        """
        logfn : Callback logging
        client_send : Sending packets from connectionbox
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.logfn = logfn
        self.client_send = client_send

        # Top status text...
        self.status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.status_box.set_margin_top(5)
        self.append(self.status_box)

        self.status_text = Gtk.Label(label="No Command in Progress")
        self.status_text.set_size_request(200, -1)
        self.status_bar = Gtk.ProgressBar()
        self.status_bar.set_hexpand(True)
        self.status_bar.set_valign(Gtk.Align.CENTER)
        self.status_bar.set_fraction(0.0)
        self.status_box.append(self.status_text)
        self.status_box.append(self.status_bar)

        # Command buttons
        self.command_colbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, homogeneous=True)
        self.append(self.command_colbox)

        self.long_commandbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.command_colbox.append(self.long_commandbox)
        self.long_commandbox_title = Gtk.Label(label="Long Commands")
        self.long_commandbox.append(self.long_commandbox_title)
        self.long_command_btn_stand = Gtk.Button(label="Lying Down -> Stand")
        self.long_command_btn_stand.connect("clicked", self.on_command_stand)
        self.long_command_btn_stand.set_size_request(-1, 60)
        self.long_command_btn_stand.set_hexpand(True)
        self.long_commandbox.append(self.long_command_btn_stand)

        self.command_queue = deque()
        self.command_sent = 0
        self.command_length = 0
        self.command_received = False
        self.command_name = "<NO COMMAND>"

    def on_command_stand(self, btn):
        # From lying down, stand up
        positions = [
            [2270, 1333, 795, 1729, 1159, 3797, 1746, 1132, 3635, 2329, 1052, 516],
            [2205, 1964, 1007, 1782, 1867, 3320, 1855, 1909, 3278, 2367, 1763, 905],
            [2313, 1357, 821, 1711, 1462, 3360, 1723, 1343, 3348, 2362, 1315, 831],
            [2314, 1357, 821, 1711, 1462, 3360, 1723, 1344, 3348, 2362, 1316, 831],
        ]
        self._send_position_command("Stand", positions)

    def _send_position_command(self, name, positions):
        """
        Runs a command which is a sequence of positions.
        """
        if len(self.command_queue) > 0:
            # cannot run command yet...
            return
        if len(positions) == 0:
            raise ValueError("Expected some positions")

        self.command_sent = 0
        self.command_length = len(positions)
        self.command_received = True
        self.command_name = name
        for pos in positions:
            self.command_queue.append(slipp.Packet(
                op="move_all_servos",
                contents={"args": copy.copy(pos)},
            ))

        self.status_text.set_text(f"Running {self.command_name} command")
        self.status_bar.set_fraction(0.0)

    def _ack_command(self, pkt):
        if pkt.op == "ACK":
            self.command_received = True
        else:
            self.command_received = False
            self.status_text.set_text(f"Command {self.command_name} failed")
            self.command_queue.clear()

    def refresh(self):
        if len(self.command_queue) > 0:
            pkt = self.command_queue.popleft()
            if self.command_received:
                self.client_send(pkt, on_recv_callback=self._ack_command)
                self.command_sent += 1
                self.command_received = False
                self.status_bar.set_fraction(self.command_sent / self.command_length)
                if self.command_sent == self.command_length:
                    self.status_text.set_text(f"Command {self.command_name} done")
