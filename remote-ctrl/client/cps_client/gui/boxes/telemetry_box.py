import itertools

from .._gtk4 import GLib, Gtk, Gdk, Pango

from ... import slipp, utils

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

class TelemetryBox(Gtk.Box):
    """
    A Telemetry box for reading telemetry from the spider.
    """
    def __init__(self, logfn, client_send, refresh_rate_ms=1000):
        """
        logfn : Callback logging
        client_send : Sending packets from connectionbox
        """
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self.logfn = logfn
        self.client_send = client_send
        self.refresh_rate_ms = refresh_rate_ms
        self.waiting_for_tm = False

        self.left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.append(self.left_col)
        self.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self.append(self.right_col)
        self.left_col.set_margin_start(5)
        self.right_col.set_margin_end(5)

        self.leg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.left_col.append(self.leg_box)

        # Create all text readings
        self.LEG_ORDER = ["front_left", "front_right", "back_left", "back_right"]
        self.JOINT_ORDER = ["inner_shoulder", "outer_shoulder", "elbow"]

        # Start with initial order, then do one read-back from the server.
        self.servo_order = DEFAULT_SERVO_ORDER
        self.synced_servo_order = False

        entry_attrs = Pango.AttrList()
        entry_attrs.insert(Pango.AttrFontDesc.new(Pango.FontDescription("Monospace")))

        title_attrs = Pango.AttrList()
        title_attrs.insert(Pango.attr_weight_new(Pango.Weight.BOLD))

        self.leg_objects = dict()
        self.servo_id_lookup = dict()
        for leg in self.LEG_ORDER:
            if len(self.leg_objects) > 0:
                sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
                self.leg_box.append(sep)

            self.leg_objects[leg] = dict()

            b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            b.set_hexpand(True)
            self.leg_box.append(b)
            self.leg_objects[leg]["box"] = b

            s = " ".join([p.capitalize() for p in leg.split("_")])
            leg_label = Gtk.Label(label=s)
            leg_label.set_margin_top(5)
            leg_label.set_margin_bottom(10)
            leg_label.set_attributes(title_attrs)
            b.append(leg_label)

            for jnt in self.JOINT_ORDER:
                s = " ".join([p.capitalize() for p in jnt.split("_")])
                servo_id = "".join([w[0] for w in leg.split("_")]) + "_" + jnt
                servo_id = servo_id.upper()
                assert servo_id in self.servo_order
                button = Gtk.Button(label=s)
                button.connect("clicked", lambda btn, id: self.change_joint_focus(id), servo_id)
                entry = Gtk.Entry()
                entry.set_editable(False)
                entry.set_attributes(entry_attrs)
                entry.set_alignment(0.5) # center
                entry.set_margin_bottom(10)
                b.append(button)
                b.append(entry)
                self.leg_objects[leg][jnt] = {
                    "button": button,
                    "entry": entry,
                    "raw_values": {},
                    "servo_id": servo_id,
                }
                self.servo_id_lookup[servo_id] = (leg, jnt)

        self.left_col.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        self.joint_status_scroll = Gtk.ScrolledWindow()
        self.joint_status_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.joint_status_scroll.set_vexpand(True)
        self.left_col.append(self.joint_status_scroll)

        self.joint_status_text = Gtk.TextBuffer()
        self.joint_status_text.set_text("DATA TO BE SHOWN HERE")

        self.joint_status_textview = Gtk.TextView(buffer=self.joint_status_text)
        self.joint_status_textview.set_editable(False)
        self.joint_status_textview.set_cursor_visible(False)
        self.joint_status_textview.set_monospace(True)
        self.joint_status_scroll.set_child(self.joint_status_textview)
        self.joint_status_active_joint = self.servo_order[0]

        self.update_leg_texts()

        # Add toggle for which metric to display it as
        self.metric_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.right_col.append(self.metric_box)
        self.metric_check_degrees = Gtk.CheckButton.new_with_label("Degrees")
        self.metric_check_degrees.set_active(True)
        self.metric_check_degrees.set_margin_top(5)
        self.metric_check_degrees.connect("toggled", self.on_metric_toggle)
        self.metric_check_radians = Gtk.CheckButton.new_with_label("Radians")
        self.metric_check_radians.set_group(self.metric_check_degrees)
        self.metric_check_radians.connect("toggled", self.on_metric_toggle)
        self.metric_check_raw = Gtk.CheckButton.new_with_label("Raw Values")
        self.metric_check_raw.set_group(self.metric_check_degrees)
        self.metric_check_raw.connect("toggled", self.on_metric_toggle)
        self.metric_box.append(self.metric_check_degrees)
        self.metric_box.append(self.metric_check_radians)
        self.metric_box.append(self.metric_check_raw)
        self.metric_box.set_margin_bottom(10)

        # Buttons for random things
        self.btn_enable_torque = Gtk.Button(label="Enable Torque")
        self.btn_enable_torque.connect("clicked", self.on_enable_torque)
        self.btn_enable_torque.set_size_request(100, 30)
        self.right_col.append(self.btn_enable_torque)

        self.btn_disable_torque = Gtk.Button(label="Disable Torque")
        self.btn_disable_torque.connect("clicked", self.on_disable_torque)
        self.btn_disable_torque.set_size_request(100, 30)
        self.right_col.append(self.btn_disable_torque)

        self.entry_torque_status = Gtk.Entry()
        self.entry_torque_status.set_text("<NO STATUS YET>")
        self.entry_torque_status.set_editable(False)
        self.entry_torque_status.set_attributes(entry_attrs)
        self.entry_torque_status.set_size_request(100, 30)
        self.right_col.append(self.entry_torque_status)

        self.btn_reboot = Gtk.Button(label="Reboot")
        self.btn_reboot.connect("clicked", self.on_reboot)
        self.set_margin_top(10)
        self.btn_reboot.set_size_request(100, 30)
        self.right_col.append(self.btn_reboot)

        self.status_duration_label = Gtk.Label(label="Duration")
        self.status_duration_label.set_margin_top(10)
        #self.status_duration_label.set_attributes(title_attrs)
        self.right_col.append(self.status_duration_label)

        self.status_duration_entry = Gtk.Entry()
        self.status_duration_entry.set_text("<NO STATUS YET>")
        self.status_duration_entry.set_editable(False)
        self.status_duration_entry.set_attributes(entry_attrs)
        self.status_duration_entry.set_size_request(100, 30)
        self.right_col.append(self.status_duration_entry)

        self.status_acceleration_label = Gtk.Label(label="Acceleration")
        self.status_acceleration_label.set_margin_top(10)
        #self.status_acceleration_label.set_attributes(title_attrs)
        self.right_col.append(self.status_acceleration_label)

        self.status_acceleration_entry = Gtk.Entry()
        self.status_acceleration_entry.set_text("<NO STATUS YET>")
        self.status_acceleration_entry.set_editable(False)
        self.status_acceleration_entry.set_attributes(entry_attrs)
        self.status_acceleration_entry.set_size_request(100, 30)
        self.right_col.append(self.status_acceleration_entry)

        self.start_refresh()

    def update_leg_texts(self):
        for leg, jnt in itertools.product(self.LEG_ORDER, self.JOINT_ORDER):
            raw_v = self.leg_objects[leg][jnt]["raw_values"].get("PRESENT_POSITION")
            servo_id = self.leg_objects[leg][jnt]["servo_id"]
            if raw_v is not None:
                if self.metric_check_degrees.get_active():
                    v = utils.dynamixel.raw_to_degrees(int(raw_v), key=servo_id)
                    self.leg_objects[leg][jnt]["entry"].set_text(f"{float(v):.04f}")
                elif self.metric_check_radians.get_active():
                    v = utils.dynamixel.raw_to_radians(int(raw_v), key=servo_id)
                    self.leg_objects[leg][jnt]["entry"].set_text(f"{float(v):.04f}")
                else:
                    self.leg_objects[leg][jnt]["entry"].set_text(f"{int(raw_v)}")
            else:
                self.leg_objects[leg][jnt]["entry"].set_text(f"{servo_id}")
            self.leg_objects[leg][jnt]["button"].add_css_class("white-button")
            self.leg_objects[leg][jnt]["button"].remove_css_class("lightblue-button")

        (leg, jnt) = self.servo_id_lookup[self.joint_status_active_joint]
        status_lines = [f"[{self.joint_status_active_joint}]"]
        for k, v in self.leg_objects[leg][jnt]["raw_values"].items():
            status_lines.append(f"{k}: {v}")
        self.joint_status_text.set_text("\n".join(status_lines))
        self.leg_objects[leg][jnt]["button"].add_css_class("lightblue-button")
        self.leg_objects[leg][jnt]["button"].remove_css_class("white-button")

    def change_joint_focus(self, new_id):
        self.joint_status_active_joint = new_id
        self.update_leg_texts()

    def on_metric_toggle(self, chk):
        self.update_leg_texts()

    def refresh(self):
        """Periodic refresh function."""
        def update_servo_order(pkt):
            self.servo_order = pkt.contents
            self.synced_servo_order = True

        if not self.synced_servo_order:
            self.client_send(slipp.Packet("get_servos"), on_recv_callback=update_servo_order)


        def update_duration(pkt):
            self.status_duration_entry.set_text(str(pkt.contents))

        self.client_send(slipp.Packet("get_duration"), on_recv_callback=update_duration)

        def update_acceleration(pkt):
            self.status_acceleration_entry.set_text(str(pkt.contents))

        self.client_send(slipp.Packet("get_acceleration"), on_recv_callback=update_acceleration)


        def update_values(pkt):
            self.waiting_for_tm = False
            if pkt.op != "ACK":
                return None
            for i, servo_id in enumerate(self.servo_order):
                leg, jnt = self.servo_id_lookup[servo_id]
                self.leg_objects[leg][jnt]["raw_values"] = {
                    k: v[i]
                    for k, v in pkt.contents.items()
                }
            self.update_leg_texts()

            torque_txt = "disabled"
            if min(pkt.contents["TORQUE_ENABLE"]) == 1:
                torque_txt = "enabled"
            self.entry_torque_status.set_text(torque_txt)

        def tm_timeout():
            self.waiting_for_tm = False

        if not self.waiting_for_tm:
            ok = self.client_send(
                slipp.Packet("read_all_servos"),
                on_recv_callback=update_values,
                on_timeout_callback=tm_timeout,
                ttl=2.0)
            if ok:
                self.waiting_for_tm = True
        self.start_refresh()

    def start_refresh(self):
        GLib.timeout_add(self.refresh_rate_ms, self.refresh)

    def on_enable_torque(self, btn):
        self.logfn("Telemetry", "enabling torque")
        self.client_send(slipp.Packet("enable_torque"))

    def on_disable_torque(self, btn):
        self.logfn("Telemetry", "disabling torque")
        self.client_send(slipp.Packet("disable_torque"))

    def on_reboot(self, btn):
        self.logfn("Telemetry", "rebooting")
        self.client_send(slipp.Packet("reboot_all_servos"))
