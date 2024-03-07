import copy
import json
import numpy as np
import os
import pathlib
import time

from collections import deque
from datetime import datetime, timezone

from .._gtk4 import GLib, Gtk, Gdk, pango_attrlist
from ..gui_types import Refresher

from ...import slipp, utils


# Testing a standup position
STANDUP_DEGREE_POS = [
    [ -30,  80,   0,  # BR
       30,  80,   0,  # FR
       30,  80,   0,  # BL
      -30,  80,   0], # FL
    [ -30,  80, 130,
       30,  80, 130,
       30,  80, 130,
      -30,  80, 130],
    [ -30,  35, 120,
       30,  35, 120,
       30,  35, 120,
      -30,  35, 120],
    # Move legs inwards
    [ -30,  35, 120,
       30,  65, 140,
       30,  65, 140,
      -30,  35, 120],
    [ -30,  35, 120,
       30,  35, 140,
       30,  35, 140,
      -30,  35, 120],
    [ -30,  65, 140,
       30,  35, 140,
       30,  35, 140,
      -30,  65, 140],
    [ -30,  35, 140,
       30,  35, 140,
       30,  35, 140,
      -30,  35, 140],
    [ -30,  60, 140,
       30,  60, 140,
       30,  60, 140,
      -30,  60, 140],
]


class ControlBox(Refresher, Gtk.Box):
    """
    A Control box for sending motion commands to the spider.
    """
    def __init__(self, main_utils):
        """
        main_utils : Class with shared utilities from the MainWindow.
        """
        # Initialize this as a refreshing object
        Refresher.__init__(self, refresh_rate_ms=250)

        # Setup box
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.set_margin_top(5)

        self.main_utils = main_utils

        # Top status text
        self.status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.append(self.status_box)

        self.status_text = Gtk.Label(label="No Command in Progress")
        self.status_text.set_margin_start(5)
        self.status_text.set_size_request(200, -1)
        self.status_bar = Gtk.ProgressBar()
        self.status_bar.set_hexpand(True)
        self.status_bar.set_valign(Gtk.Align.CENTER)
        self.status_bar.set_fraction(0.0)
        self.status_bar.set_margin_end(5)
        self.status_box.append(self.status_text)
        self.status_box.append(self.status_bar)

        # Top control bar
        self.control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.append(self.control_box)

        self.control_btn_run = Gtk.Button(label="Run Command")
        self.control_btn_run.connect("clicked", self.on_run_command)
        self.control_btn_run.set_size_request(-1, 50)
        self.control_btn_run.set_hexpand(True)
        self.control_btn_run.set_margin_start(5)
        self.control_box.append(self.control_btn_run)

        self.control_btn_stop = Gtk.Button(label="Stop Command")
        self.control_btn_stop.connect("clicked", self.on_stop_command)
        self.control_btn_stop.set_size_request(-1, 50)
        self.control_btn_stop.add_css_class("red-button")
        self.control_btn_stop.set_hexpand(True)
        self.control_box.append(self.control_btn_stop)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_start(10)
        sep.set_margin_end(10)
        self.control_box.append(sep)

        self.control_duration_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.control_box.append(self.control_duration_box)
        self.control_duration_label = Gtk.Label(label="Duration")
        self.control_duration_entry = self.main_utils.cache.CacheEntry("CMD_DURATION", default="600")
        self.control_duration_entry.set_alignment(0.5)
        self.control_duration_entry.set_max_width_chars(9)
        self.control_duration_box.append(self.control_duration_label)
        self.control_duration_box.append(self.control_duration_entry)

        self.control_acceleration_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.control_box.append(self.control_acceleration_box)
        self.control_acceleration_label = Gtk.Label(label="Acceleration")
        self.control_acceleration_entry = self.main_utils.cache.CacheEntry("CMD_ACCELERATION", default="200")
        self.control_acceleration_entry.set_alignment(0.5)
        self.control_acceleration_entry.set_max_width_chars(9)
        self.control_acceleration_box.append(self.control_acceleration_label)
        self.control_acceleration_box.append(self.control_acceleration_entry)

        self.control_btn_update = Gtk.Button(label="Set Values")
        self.control_btn_update.connect("clicked", self.on_update_duration_accceleration)
        self.control_btn_update.set_size_request(-1, 50)
        self.control_btn_update.set_margin_end(5)
        self.control_box.append(self.control_btn_update)

        self.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Split into columns (left = edit, right = narrow predef buttons)
        self.command_colbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.append(self.command_colbox)

        # Command editor box and title
        self.command_edit_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.command_edit_box.set_margin_start(10)
        self.command_colbox.append(self.command_edit_box)
        self.command_edit_title = Gtk.Label(label="Command Editor")
        self.command_edit_title.set_attributes(pango_attrlist(textsize=14))
        self.command_edit_box.append(self.command_edit_title)

        # Some option boxes
        self.command_editopt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.command_edit_box.append(self.command_editopt_box)
        # Command repeat
        self.command_editopt_repeat_label = Gtk.Label(label="Repeat")
        self.command_editopt_repeat_entry = self.main_utils.cache.CacheEntry("CMD_REPEAT", default="4")
        self.command_editopt_repeat_entry.set_alignment(0.5)
        self.command_editopt_repeat_entry.set_max_width_chars(2)
        self.command_editopt_box.append(self.command_editopt_repeat_label)
        self.command_editopt_box.append(self.command_editopt_repeat_entry)
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_start(10)
        sep.set_margin_end(10)
        self.command_editopt_box.append(sep)
        # Command dt
        self.command_editopt_timedelta_label = Gtk.Label(label="Time delta [ms]")
        self.command_editopt_timedelta_entry = self.main_utils.cache.CacheEntry("CMD_TIMEDELTA", default="250")
        self.command_editopt_timedelta_entry.set_alignment(0.5)
        self.command_editopt_timedelta_entry.set_max_width_chars(4)
        self.command_editopt_box.append(self.command_editopt_timedelta_label)
        self.command_editopt_box.append(self.command_editopt_timedelta_entry)
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_start(10)
        sep.set_margin_end(10)
        self.command_editopt_box.append(sep)
        # Command units
        self.command_editopt_metric_degrees = Gtk.CheckButton.new_with_label("Degrees")
        self.command_editopt_metric_degrees.set_active(True)
        self.command_editopt_metric_degrees.connect("toggled", self.on_metric_toggle)
        self.command_editopt_metric_radians = Gtk.CheckButton.new_with_label("Radians")
        self.command_editopt_metric_radians.set_group(self.command_editopt_metric_degrees)
        self.command_editopt_metric_radians.connect("toggled", self.on_metric_toggle)
        self.command_editopt_metric_raw = Gtk.CheckButton.new_with_label("Raw Values")
        self.command_editopt_metric_raw.set_group(self.command_editopt_metric_degrees)
        self.command_editopt_metric_raw.connect("toggled", self.on_metric_toggle)
        self.command_editopt_box.append(self.command_editopt_metric_degrees)
        self.command_editopt_box.append(self.command_editopt_metric_radians)
        self.command_editopt_box.append(self.command_editopt_metric_raw)
        self.command_editopt_metric_last_active = "degrees"
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_start(10)
        sep.set_margin_end(10)
        self.command_editopt_box.append(sep)
        # Toggle to save data from run
        self.command_editopt_record_label = Gtk.Label(label="Record Trajectory")
        self.command_editopt_record_switch = Gtk.Switch()
        self.command_editopt_record_switch.set_active(False)
        self.command_editopt_box.append(self.command_editopt_record_label)
        self.command_editopt_box.append(self.command_editopt_record_switch)

        # The actual editor window
        self.command_edit_scroll = Gtk.ScrolledWindow()
        self.command_edit_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.command_edit_scroll.set_vexpand(True)
        self.command_edit_scroll.set_hexpand(True)
        self.command_edit_scroll.set_margin_bottom(5)
        self.command_edit_box.append(self.command_edit_scroll)

        self.command_edit_buffer = Gtk.TextBuffer()
        self.command_edit_buffer.set_text("")

        self.command_edit_textview = Gtk.TextView(buffer=self.command_edit_buffer)
        self.command_edit_textview.set_editable(True)
        self.command_edit_textview.set_cursor_visible(True)
        self.command_edit_textview.set_monospace(True)
        self.command_edit_textview.set_left_margin(10)
        self.command_edit_textview.set_right_margin(10)
        self.command_edit_textview.set_top_margin(10)
        self.command_edit_textview.set_bottom_margin(10)
        self.command_edit_textview.add_css_class("commandbox-edit-textview")
        self.command_edit_textview.set_margin_bottom(5)
        self.command_edit_scroll.set_child(self.command_edit_textview)

        # Separator between editor and predefined commands
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.command_colbox.append(sep)

        # Predefined commands
        self.long_commandbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.long_commandbox.set_margin_end(5)
        self.long_commandbox_title = Gtk.Label(label="Predefined Commands")
        self.long_commandbox.append(self.long_commandbox_title)
        self.command_colbox.append(self.long_commandbox)

        COMMANDS = [
            ("Stand Up", self.on_command_stand_up),
            ("Lie Down From Stand", self.on_command_liedown_from_stand),
            ("Trot", self.on_command_trot),
            ("Creep", self.on_command_creep),
            ("Trot (v2)", self.on_command_trot_johnmod),
            ("Lie Down", self.on_command_liedown),
            ("Stand", self.on_command_stand),
        ]

        for tup in COMMANDS:
            cmd = tup[0]
            connect_args = tup[1:]
            btn = Gtk.Button(label=cmd)
            btn.connect("clicked", *connect_args)
            btn.set_size_request(-1, 40)
            self.long_commandbox.append(btn)

        self.command_queue = deque()
        self.command_sent = 0
        self.command_length = 0
        self.command_received = False
        self.telemetry_received = False
        self.command_name = "<NO COMMAND>"
        # For saving incoming data
        self.command_sent_positions = []
        self.command_recv_telemetry = []

        self.start_refresh()

    def set_error_status(self, txt, notify=False):
        """Sets an error status message."""
        self.status_text.set_text(txt)
        self.status_bar.set_fraction(1.0)
        self.status_bar.add_css_class("progress-bar-red")
        if notify:
            self.main_utils.notify(txt)

    def set_ok_status(self, txt, frac=1.0, notify=False):
        """Sets an regular status message."""
        self.status_text.set_text(txt)
        self.status_bar.set_fraction(frac)
        self.status_bar.remove_css_class("progress-bar-red")
        if notify:
            self.main_utils.notify(txt, success=True)

    def on_stop_command(self, btn):
        self._stop_running_command(f"Command interrupted")

    def on_command_stand_up(self, btn):
        # From lying down, stand up
        self._set_command_in_degrees(STANDUP_DEGREE_POS)

    def on_command_liedown_from_stand(self, btn):
        # From lying down, stand up
        self._set_command_in_degrees(
            list(reversed(STANDUP_DEGREE_POS)) + [[0.0]*12]
        )

    def on_command_liedown(self, btn):
        # Go to lying down position
        self._set_command_in_degrees([[0.0]*12])

    def on_command_stand(self, btn):
        # Go to lying down position
        self._set_command_in_degrees([STANDUP_DEGREE_POS[-1]])

    def on_metric_toggle(self, chk):
        has_error = False
        try:
            raw_values = self._get_command_raw_values()
        except Exception as e:
            self.set_error_status(f"Invalid Command Format")
            has_error = True

        if self.command_editopt_metric_degrees.get_active():
            self.command_editopt_metric_last_active = "degrees"
        elif self.command_editopt_metric_radians.get_active():
            self.command_editopt_metric_last_active = "radians"
        else:
            self.command_editopt_metric_last_active = "raw"

        if has_error:
            return

        if self.command_editopt_metric_degrees.get_active():
            values = [self._rawpos_to_degrees(rw) for rw in raw_values]
        elif self.command_editopt_metric_radians.get_active():
            values = [self._rawpos_to_radians(rw) for rw in raw_values]
        else:
            values = raw_values

        self._set_commandseq(values)

    def _get_command_raw_values(self):
        """Retrieve the raw values of the data stored in the command editor."""
        raw_text = self.command_edit_buffer.get_text(
            self.command_edit_buffer.get_start_iter(),
            self.command_edit_buffer.get_end_iter(),
            False,
        )
        raw_text = raw_text.strip()
        if raw_text.endswith(","):
            raw_text = raw_text[:-1]

        raw_values = json.loads(f"[{raw_text}]")
        if self.command_editopt_metric_last_active == "degrees":
            raw_values = [self._degrees_to_rawpos(rw) for rw in raw_values]
        elif self.command_editopt_metric_last_active == "radians":
            raw_values = [self._radians_to_rawpos(rw) for rw in raw_values]
        return raw_values

    def _set_command_in_degrees(self, commandseq):
        self.command_editopt_metric_degrees.set_active(True)
        self._set_commandseq(commandseq)

    def _set_command_in_radians(self, commandseq):
        self.command_editopt_metric_radians.set_active(True)
        self._set_commandseq(commandseq)

    def _set_commandseq(self, commandseq):
        max_vlen = -1
        str_commandseq = [
            [
                f"{v:.5g}" if isinstance(v, float) else json.dumps(v)
                for v in cmd
            ]
            for cmd in commandseq
        ]
        for cmd in str_commandseq:
            for v in cmd:
                max_vlen = max(max_vlen, len(v))

        lines = []
        curline = ""
        for cmd in str_commandseq:
            if len(lines) > 0:
                lines[-1] += ","
            curline = "["
            for i, v in enumerate(cmd):
                curline += " "*(1 + max_vlen - len(v)) + v
                if (i + 1) < len(cmd):
                    curline += ","
                else:
                    curline += "]"
                if (i+1) % 3 == 0:
                    lines.append(curline)
                    curline = " "
            if len(curline.strip()) > 0:
                lines.append(curline)

        self.command_edit_buffer.set_text("\n".join(lines))


    def _rawpos_to_degrees(self, pos):
        return [utils.dynamixel.raw_to_degrees(p,k) for p,k in zip(pos, self.main_utils.cache.get("SERVO_ORDER"))]
    
    def _rawpos_to_radians(self, pos):
        return [utils.dynamixel.raw_to_radians(p,k) for p,k in zip(pos, self.main_utils.cache.get("SERVO_ORDER"))]
    
    def _degrees_to_rawpos(self, pos):
        return [utils.dynamixel.degrees_to_raw(p,k) for p,k in zip(pos, self.main_utils.cache.get("SERVO_ORDER"))]
    
    def _radians_to_rawpos(self, pos):
        return [utils.dynamixel.radians_to_raw(p,k) for p,k in zip(pos, self.main_utils.cache.get("SERVO_ORDER"))]

    def _reverse_gait(self, gait_fn):
        def revgait():
            return tuple(list(reversed(t)) for t in gait_fn())
        return revgait

    def on_command_trot(self, btn):
        self._on_martin_gait(
            gait_fn=utils.martin_control.trot_gait,
            dt=(1 / utils.martin_control.TROT_HZ) * 2,
        )

    def on_command_creep(self, btn):
        self._on_martin_gait(
            gait_fn=utils.martin_control.creep_gait,
            dt=(1 / utils.martin_control.CREEP_HZ),
        )

    def on_command_trot_johnmod(self, btn):
        self._on_martin_gait(
            gait_fn=utils.martin_control.trot_gait_johnmod,
            dt=(1 / utils.martin_control.TROT_HZ) * 2,
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
        for i in range(32):
            #action_idx = i % len(back_right_joints)
            action_idx = int(i * 0.25 / dt) % len(back_right_joints)
            pos = [
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
            ]
            positions.append(pos)

        self._set_command_in_radians(positions)

    def on_run_command(self, btn):
        """
        Runs the command which is entered in the editor.
        """
        if len(self.command_queue) > 0:
            # cannot run command yet...
            return

        try:
            raw_values = self._get_command_raw_values()
            assert len(raw_values) > 0
        except Exception as e:
            self.set_error_status(f"Invalid Command Format")
            return

        try:
            repeat = int(self.command_editopt_repeat_entry.get_text())
            assert repeat > 0
        except Exception as e:
            self.set_error_status(f"Invalid Repeat Value (must be a positive integer)")
            return

        try:
            command_dt_ms = int(self.command_editopt_timedelta_entry.get_text())
            assert command_dt_ms >= 100
        except Exception as e:
            self.set_error_status(f"Invalid Timedelta Value (expected int >= 100)")
            return

        positions = []
        for rw in raw_values:
            for _ in range(repeat):
                positions.append(rw)

        self.command_sent = 0
        self.command_length = len(positions)
        self.command_received = True
        self.telemetry_received = True
        self.command_sent_positions = []
        self.command_recv_telemetry = []
        for pos in positions:
            self.command_queue.append(copy.copy(pos))

        self.set_ok_status(
            f"Running command ({self.command_sent}/{self.command_length})",
            frac=0.0,
        )
        self.set_refresh_rate(command_dt_ms)


    def on_update_duration_accceleration(self, btn):
        v_duration = int(self.control_duration_entry.get_text())
        v_accel = int(self.control_acceleration_entry.get_text())
        self.main_utils.client_send(slipp.Packet("set_duration", contents={"args": [v_duration]}))
        self.main_utils.client_send(slipp.Packet("set_acceleration", contents={"args": [v_accel]}))

    def _ack_command(self, pkt):
        if pkt.op == "ACK":
            self.command_received = True
            self.command_sent_positions[-1]["robot_ack_timestamp"] = pkt.timestamp_seconds
        else:
            self._stop_running_command("Command failed", notify=True)

    def _ack_telemetry(self, pkt):
        if pkt.op == "ACK":
            self.telemetry_received = True
            self.command_recv_telemetry.append({
                "client_timestamp": datetime.now(timezone.utc).timestamp(),
                "robot_timestamp": pkt.timestamp_seconds,
                "contents": pkt.contents["data"],
                "tm_pkt": pkt.blob,
            })
        else:
            self._stop_running_command("Telemetry read failed", notify=True)

    def _timeout_command(self):
        self._stop_running_command("Command timed out", notify=True)

    def _stop_running_command(self, errmsg=None, okmsg=None, notify=False):
        if self.command_length > 0:
            self.command_received = False
            self.telemetry_received = False
            self.command_queue.clear()
            self.command_sent = 0
            self.command_length = 0
            self.command_sent_positions = []
            self.command_recv_telemetry = []
            self.set_refresh_rate(250)
            if errmsg is not None:
                self.set_error_status(errmsg, notify=notify)
            elif okmsg is not None:
                self.set_ok_status(okmsg, notify=notify)

    def refresh(self):
        if len(self.command_queue) > 0:
            if self.command_received and self.telemetry_received:
                pos = self.command_queue.popleft()
                cmd_pkt = slipp.Packet("move_all_servos_steady", contents={"args": copy.copy(pos)})
                tm_pkt = slipp.Packet("read_all_servos_RAM")
                self.main_utils.client_send(
                    cmd_pkt,
                    on_recv_callback=self._ack_command,
                    on_timeout_callback=self._timeout_command,
                    # Maybe set a smaller TTL?
                    ttl=5.0,
                )
                self.main_utils.client_send(
                    tm_pkt,
                    on_recv_callback=self._ack_telemetry,
                    on_timeout_callback=self._timeout_command,
                    # Maybe set a smaller TTL?
                    ttl=5.0,
                )
                self.command_sent += 1
                self.command_sent_positions.append({
                    "client_timestamp": datetime.now(timezone.utc).timestamp(),
                    "positions": pos,
                    "cmd_pkt": cmd_pkt.blob,
                })
                self.command_received = False
                self.telemetry_received = False
                self.set_ok_status(
                    f"Running command ({self.command_sent}/{self.command_length})",
                    frac=self.command_sent / self.command_length,
                )
        elif self.command_sent == self.command_length and self.command_received and self.telemetry_received:
            if self.command_editopt_record_switch.get_active():
                dstdir = self.main_utils.cache.cachedir / "runs"
                os.makedirs(dstdir, exist_ok=True)
                dstfile = dstdir / datetime.now().strftime("ctrl-%Y-%m-%d_%H%M%S.json")
                contents = {
                    "servo_order": self.main_utils.cache.get("SERVO_ORDER"),
                    "sent_positions": self.command_sent_positions,
                    "recv_telemetry": self.command_recv_telemetry,
                }
                try:
                    with open(dstfile, "w+") as f:
                        json.dump(contents, f)
                except Exception as e:
                    self.main_utils.notify(f"Error saving control trajectory: {str(e)}")
                else:
                    self.main_utils.notify(f"Saved trajectory as {str(dstfile)}", success=True)

            self._stop_running_command(okmsg=f"Command done")
