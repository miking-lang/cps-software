import copy
import numpy as np

from collections import deque

from .._gtk4 import GLib, Gtk, Gdk

from ...import slipp, utils

SERVO_ORDER = [
    "FL_INNER_SHOULDER",
    "FL_OUTER_SHOULDER",
    "FL_ELBOW",
    "FR_INNER_SHOULDER",
    "FR_OUTER_SHOULDER",
    "FR_ELBOW",
    "BL_INNER_SHOULDER",
    "BL_OUTER_SHOULDER",
    "BL_ELBOW",
    "BR_INNER_SHOULDER",
    "BR_OUTER_SHOULDER",
    "BR_ELBOW",
]

def rawpos_to_degrees(pos):
    return [utils.dynamixel.raw_to_degrees(p,k) for p,k in zip(pos, SERVO_ORDER)]

def rawpos_to_radians(pos):
    return [utils.dynamixel.raw_to_radians(p,k) for p,k in zip(pos, SERVO_ORDER)]

def degrees_to_rawpos(pos):
    return [utils.dynamixel.degrees_to_raw(p,k) for p,k in zip(pos, SERVO_ORDER)]

def radians_to_rawpos(pos):
    return [utils.dynamixel.radians_to_raw(p,k) for p,k in zip(pos, SERVO_ORDER)]



class CommandBox(Gtk.Box):
    """
    A Command box for sending motion commands to the spider.
    """
    def __init__(self, logfn, client_send, refresh_rate_ms=250):
        """
        logfn : Callback logging
        client_send : Sending packets from connectionbox
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.logfn = logfn
        self.client_send = client_send
        self.refresh_rate_ms = refresh_rate_ms

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
        self.long_commandbox_title = Gtk.Label(label="Long Commands")
        self.long_commandbox.append(self.long_commandbox_title)
        self.command_colbox.append(self.long_commandbox)

        stopbtn = Gtk.Button(label="Stop Command")
        stopbtn.connect("clicked", self.on_stop_command)
        stopbtn.set_size_request(-1, 60)
        stopbtn.add_css_class("red-button")
        stopbtn.set_hexpand(True)
        self.long_commandbox.append(stopbtn)

        COMMANDS = [
            ("Stand", self.on_command_stand),
            ("Lie Down", self.on_command_liedown),
            ("Trot", self.on_command_trot),
        ]

        for cmd, cmdfn in COMMANDS:
            btn = Gtk.Button(label=cmd)
            btn.connect("clicked", cmdfn)
            btn.set_size_request(-1, 60)
            btn.set_hexpand(True)
            self.long_commandbox.append(btn)

        self.command_queue = deque()
        self.command_sent = 0
        self.command_length = 0
        self.command_received = False
        self.command_name = "<NO COMMAND>"

        self.start_refresh()

    @property
    def dt(self):
        return self.refresh_rate_ms / 1000.0

    def on_stop_command(self, btn):
        if len(self.command_queue) > 0:
            self.command_queue.clear()
            self.status_text.set_text(f"Command interrupted")

    def on_command_stand(self, btn):
        # From lying down, stand up
        pos1 = [2270, 1333, 795, 1729, 1159, 3797, 1746, 1132, 3635, 2329, 1052, 516]
        pos2 = [2205, 1964, 1007, 1782, 1867, 3320, 1855, 1909, 3278, 2367, 1763, 905]
        pos3 = [2313, 1357, 821, 1711, 1462, 3360, 1723, 1343, 3348, 2362, 1315, 831]
        positions = ([pos1]*int(max(1, 1/self.dt))) + ([pos2]*int(max(1, 1/self.dt))) #+ ([pos3]*int(max(1, 1/self.dt)))

        #for i, pos in enumerate(positions):
        #    print(f"i={i} = {rawpos_to_degrees(pos)}")
        self._send_position_command("Stand", positions)

    def on_command_liedown(self, btn):
        # Go to lying down position
        positions = [
            degrees_to_rawpos([0.0]*12),
        ]
        #for i, pos in enumerate(positions):
        #    print(f"i={i} = {rawpos_to_degrees(pos)}")
        self._send_position_command("Lie Down", positions)

    def on_command_trot(self, btn):
        # Walk for a bit
        positions = []

        #for i, pos in enumerate(positions):
        #    print(f"i={i} = {rawpos_to_degrees(pos)}")

        gait_fn = utils.martin_control.trot_gait
        dt=(1 / utils.martin_control.TROT_HZ)

        (
            back_right_joints,
            back_left_joints,
            front_right_joints,
            front_left_joints,
        ) = gait_fn()
        for i in range(100):
            action_idx = int(i * self.dt / dt) % len(back_right_joints)
            pos = np.array([
                back_right_joints[action_idx][0],
                back_right_joints[action_idx][1] - 0.25,
                back_right_joints[action_idx][2] - 0.35,
                front_right_joints[action_idx][0],
                front_right_joints[action_idx][1] - 0.25,
                front_right_joints[action_idx][2] - 0.35,
                back_left_joints[action_idx][0],
                back_left_joints[action_idx][1] - 0.25,
                back_left_joints[action_idx][2] - 0.35,
                front_left_joints[action_idx][0],
                front_left_joints[action_idx][1] - 0.25,
                front_left_joints[action_idx][2] - 0.35,
            ])
            positions.append(radians_to_rawpos(list(pos)))

        #for i, pos in enumerate(positions):
        #    print(f"i={i} = {rawpos_to_degrees(pos)}")
        self._send_position_command("Trot", positions)

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

        self.status_text.set_text(f"Running {self.command_name} command ({self.command_sent}/{self.command_length})")
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
            if self.command_received:
                pkt = self.command_queue.popleft()
                self.client_send(pkt, on_recv_callback=self._ack_command)
                self.command_sent += 1
                self.command_received = False
                self.status_bar.set_fraction(self.command_sent / self.command_length)
                if self.command_sent == self.command_length:
                    self.status_text.set_text(f"Command {self.command_name} done")
                else:
                    self.status_text.set_text(f"Running {self.command_name} command ({self.command_sent}/{self.command_length})")

        self.start_refresh()

    def start_refresh(self):
        GLib.timeout_add(self.refresh_rate_ms, self.refresh)
