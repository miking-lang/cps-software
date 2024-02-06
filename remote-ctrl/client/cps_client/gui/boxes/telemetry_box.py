import itertools

from .._gtk4 import GLib, Gtk, Gdk, Pango

from ... import slipp, utils

DEFAULT_SERVO_ORDER = [
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

class TelemetryBox(Gtk.Box):
    """
    A Telemetry box for reading telemetry from the spider.
    """
    def __init__(self, logfn, client_send, refresh_rate_ms=1000):
        """
        logfn : Callback logging
        client_send : Sending packets from connectionbox
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.logfn = logfn
        self.client_send = client_send
        self.refresh_rate_ms = refresh_rate_ms

        self.leg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.append(self.leg_box)

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
                label = Gtk.Label(label=s)
                entry = Gtk.Entry()
                entry.set_editable(False)
                entry.set_attributes(entry_attrs)
                entry.set_alignment(0.5) # center
                entry.set_margin_bottom(10)
                b.append(label)
                b.append(entry)
                self.leg_objects[leg][jnt] = {
                    "label": label,
                    "entry": entry,
                    "raw_values": {},
                    "servo_id": servo_id,
                }
                self.servo_id_lookup[servo_id] = (leg, jnt)
        self.update_leg_texts()

        # Add toggle for which metric to display it as
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.leg_box.append(sep)
        self.metric_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.leg_box.append(self.metric_box)
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

        # Buttons for random things
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(self.button_box)

        self.btn_enable_torque = Gtk.Button(label="Enable Torque")
        self.btn_enable_torque.connect("clicked", self.on_enable_torque)
        self.btn_enable_torque.set_size_request(100, 30)
        self.button_box.append(self.btn_enable_torque)

        self.btn_disable_torque = Gtk.Button(label="Disable Torque")
        self.btn_disable_torque.connect("clicked", self.on_disable_torque)
        self.btn_disable_torque.set_size_request(100, 30)
        self.button_box.append(self.btn_disable_torque)

        self.entry_torque_status = Gtk.Entry()
        self.entry_torque_status.set_text("<NO STATUS YET>")
        self.entry_torque_status.set_editable(False)
        self.entry_torque_status.set_attributes(entry_attrs)
        self.entry_torque_status.set_size_request(100, 30)
        self.button_box.append(self.entry_torque_status)

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

    def on_metric_toggle(self, chk):
        self.update_leg_texts()

    def refresh(self):
        """Periodic refresh function."""
        def update_servo_order(pkt):
            self.servo_order = pkt.contents
            self.synced_servo_order = True

        if not self.synced_servo_order:
            self.client_send(slipp.Packet("get_servos"), on_recv_callback=update_servo_order)

        def update_values(pkt):
            if pkt.op != "ACK":
                return None

            for i, servo_id in enumerate(self.servo_order):
                leg, jnt = self.servo_id_lookup[servo_id]
                self.leg_objects[leg][jnt]["raw_values"] = {
                    k: v[i]
                    for k, v in pkt.contents.items()
                }

            self.update_leg_texts()
            self.entry_torque_status.set_text(str(min(pkt.contents["TORQUE_ENABLE"])))

        self.client_send(slipp.Packet("read_all"), on_recv_callback=update_values)
        self.start_refresh()

    def start_refresh(self):
        GLib.timeout_add(self.refresh_rate_ms, self.refresh)

    def on_enable_torque(self, btn):
        self.logfn("Telemetry", "enabling torque")
        self.client_send(slipp.Packet("enable_torque"))

    def on_disable_torque(self, btn):
        self.logfn("Telemetry", "disabling torque")
        self.client_send(slipp.Packet("disable_torque"))
