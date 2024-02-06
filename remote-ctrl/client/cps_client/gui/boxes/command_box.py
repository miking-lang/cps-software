import copy
import numpy as np

from collections import deque

from .._gtk4 import GLib, Gtk, Gdk

from ...import slipp, utils

SERVO_ORDER = [
    "BR_INNER_SHOULDER",
    "BR_OUTER_SHOULDER",
    "BR_ELBOW",
    "FR_INNER_SHOULDER",
    "FR_OUTER_SHOULDER",
    "FR_ELBOW",
    "BL_INNER_SHOULDER",
    "BL_OUTER_SHOULDER",
    "BL_ELBOW",
    "FL_INNER_SHOULDER",
    "FL_OUTER_SHOULDER",
    "FL_ELBOW",
]

def rawpos_to_degrees(pos):
    return [utils.dynamixel.raw_to_degrees(p,k) for p,k in zip(pos, SERVO_ORDER)]

def rawpos_to_radians(pos):
    return [utils.dynamixel.raw_to_radians(p,k) for p,k in zip(pos, SERVO_ORDER)]

def degrees_to_rawpos(pos):
    return [utils.dynamixel.degrees_to_raw(p,k) for p,k in zip(pos, SERVO_ORDER)]

def radians_to_rawpos(pos):
    return [utils.dynamixel.radians_to_raw(p,k) for p,k in zip(pos, SERVO_ORDER)]


# Testing a standup position
STANDUP_COARSE_POS = [
    degrees_to_rawpos([-20.0, 80.0, 0.0,
                        20.0, 80.0, 0.0,
                        20.0, 80.0, 0.0,
                       -20.0, 80.0, 0.0]),
    degrees_to_rawpos([-20.0, 80.0, 135.0,
                        20.0, 80.0, 135.0,
                        20.0, 80.0, 135.0,
                       -20.0, 80.0, 135.0]),
    degrees_to_rawpos([-20.0, 45.0, 135.0,
                        20.0, 45.0, 135.0,
                        20.0, 45.0, 135.0,
                       -20.0, 45.0, 135.0]),
]

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
        self.command_colbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.append(self.command_colbox)

        self.long_commandbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.long_commandbox.set_margin_start(5)
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
            ("Lie Down From Stand", self.on_command_liedown_from_stand),
            ("Trot", self.on_command_trot),
            ("Reverse Trot", self.on_command_trot, True),
            ("Creep", self.on_command_creep),
        ]

        for tup in COMMANDS:
            cmd = tup[0]
            connect_args = tup[1:]
            btn = Gtk.Button(label=cmd)
            btn.connect("clicked", *connect_args)
            btn.set_size_request(-1, 40)
            btn.set_hexpand(True)
            self.long_commandbox.append(btn)

        self.command_queue = deque()
        self.command_sent = 0
        self.command_length = 0
        self.command_received = False
        self.command_name = "<NO COMMAND>"

        self.specific_commandbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.specific_commandbox.set_margin_end(5)
        self.specific_commandbox_title = Gtk.Label(label="Specific Commands")
        self.specific_commandbox.append(self.specific_commandbox_title)
        self.command_colbox.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self.command_colbox.append(self.specific_commandbox)

        self.specific_setduration_btn = Gtk.Button(label="Set Duration")
        self.specific_setduration_btn.set_margin_top(10)
        self.specific_setduration_btn.connect("clicked", self.on_set_duration)
        self.specific_setduration_btn.set_size_request(80, 30)
        self.specific_commandbox.append(self.specific_setduration_btn)

        self.specific_setduration_entry = Gtk.Entry()
        self.specific_setduration_entry.set_text("600")
        self.specific_setduration_entry.set_size_request(80, 30)
        self.specific_commandbox.append(self.specific_setduration_entry)

        self.specific_setacceleration_btn = Gtk.Button(label="Set Acceleration")
        self.specific_setacceleration_btn.set_margin_top(10)
        self.specific_setacceleration_btn.connect("clicked", self.on_set_acceleration)
        self.specific_setacceleration_btn.set_size_request(80, 30)
        self.specific_commandbox.append(self.specific_setacceleration_btn)

        self.specific_setacceleration_entry = Gtk.Entry()
        self.specific_setacceleration_entry.set_text("200")
        self.specific_setacceleration_entry.set_size_request(80, 30)
        self.specific_commandbox.append(self.specific_setacceleration_entry)

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
        coarse_positions = STANDUP_COARSE_POS
        positions = []
        for pos in coarse_positions:
            positions += [pos]*int(max(1, 1/self.dt))

        self._send_position_command("Stand", positions)

    def on_command_liedown(self, btn):
        # Go to lying down position
        positions = [
            degrees_to_rawpos([0.0]*12),
        ]
        self._send_position_command("Lie Down", positions)

    def on_command_liedown_from_stand(self, btn):
        # From lying down, stand up
        coarse_positions = list(reversed(STANDUP_COARSE_POS))
        coarse_positions += [degrees_to_rawpos([0.0]*12)]
        positions = []
        for pos in coarse_positions:
            positions += [pos]*int(max(1, 1/self.dt))

        self._send_position_command("Lie Down from Standing", positions)

    def _reverse_gait(self, gait_fn):
        def revgait():
            return tuple(list(reversed(t)) for t in gait_fn())
        return revgait

    def on_command_trot(self, btn, reverse=False):
        gait_fn = utils.martin_control.trot_gait
        if reverse:
            gait_fn = self._reverse_gait(utils.martin_control.trot_gait)

        self._on_martin_gait(
            gait_fn=gait_fn,
            dt=(1 / utils.martin_control.TROT_HZ) * 4,
        )

    def on_command_creep(self, btn):
        self._on_martin_gait(
            gait_fn=utils.martin_control.creep_gait,
            dt=(1 / utils.martin_control.CREEP_HZ),
        )

    def _on_martin_gait(self, gait_fn, dt):
        # Walk for a bit
        positions = []

        (
            back_right_joints,
            back_left_joints,
            front_right_joints,
            front_left_joints,
        ) = gait_fn()
        for i in range(100):
            #action_idx = i % len(back_right_joints)
            action_idx = int(i * self.dt / dt) % len(back_right_joints)
            pos = np.array([
                back_right_joints[action_idx][0],
                back_right_joints[action_idx][1],
                back_right_joints[action_idx][2],
                front_right_joints[action_idx][0],
                front_right_joints[action_idx][1],
                front_right_joints[action_idx][2],
                back_left_joints[action_idx][0],
                back_left_joints[action_idx][1],
                back_left_joints[action_idx][2],
                front_left_joints[action_idx][0],
                front_left_joints[action_idx][1],
                front_left_joints[action_idx][2],
            ])
            positions.append(radians_to_rawpos(list(pos)))

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

    def on_set_duration(self, btn):
        v = int(self.specific_setduration_entry.get_text())
        self.client_send(slipp.Packet("set_duration", contents={"args": [v]}))

    def on_set_acceleration(self, btn):
        v = int(self.specific_setacceleration_entry.get_text())
        self.client_send(slipp.Packet("set_acceleration", contents={"args": [v]}))

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
