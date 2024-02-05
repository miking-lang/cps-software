from .._gtk4 import GLib, Gtk, Gdk, Pango

from ... import slipp, utils

class TelemetryBox(Gtk.Box):
    """
    A Telemetry box for reading telemetry from the spider.
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

        self.leg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.LEG_ORDER = ["front_left", "front_right", "back_left", "back_right"]
        self.JOINT_ORDER = ["inner_shoulder", "outer_shoulder", "elbow"]

        entry_attrs = Pango.AttrList()
        entry_attrs.insert(Pango.AttrFontDesc.new(Pango.FontDescription("Monospace")))

        title_attrs = Pango.AttrList()
        title_attrs.insert(Pango.attr_weight_new(Pango.Weight.BOLD))

        self.leg_objects = dict()
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
                    "raw_value": None,
                    "servo_id": servo_id,
                }
        self.update_leg_texts()

        self.append(self.leg_box)

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

        self.start_refresh()

    def update_leg_texts(self):
        for leg in self.LEG_ORDER:
            for jnt in self.JOINT_ORDER:
                raw_v = self.leg_objects[leg][jnt]["raw_value"]
                servo_id = self.leg_objects[leg][jnt]["servo_id"]
                if raw_v is not None:
                    # By default: Show degrees
                    v = utils.dynamixel.raw_to_degrees(int(raw_v), key=servo_id)
                    self.leg_objects[leg][jnt]["entry"].set_text(f"{float(v):.04f}")
                else:
                    self.leg_objects[leg][jnt]["entry"].set_text(f"{servo_id}")

    def refresh(self):
        def update_servos(pkt):
            if pkt.op != "ACK":
                return None

            i = -1
            for leg in self.LEG_ORDER:
                for jnt in self.JOINT_ORDER:
                    i += 1
                    self.leg_objects[leg][jnt]["raw_value"] = pkt.contents[i]
            self.update_leg_texts()

        self.client_send(slipp.Packet("read_all_servo_positions"), on_recv_callback=update_servos)
        self.start_refresh()

    def start_refresh(self):
        GLib.timeout_add(self.refresh_rate_ms, self.refresh)

    def on_enable_torque(self, btn):
        self.logfn("Telemetry", "enabling torque")
        self.client_send(slipp.Packet("enable_torque"))

    def on_disable_torque(self, btn):
        self.logfn("Telemetry", "disabling torque")
        self.client_send(slipp.Packet("disable_torque"))
