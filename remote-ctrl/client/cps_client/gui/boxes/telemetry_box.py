from .._gtk4 import GLib, Gtk, Gdk

from ...import slipp

class TelemetryBox(Gtk.Box):
    """
    A Telemetry box for reading telemetry from the spider.
    """
    def __init__(self, logfn, client_send):
        """
        logfn : Callback logging
        client_send : Sending packets from connectionbox
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.logfn = logfn
        self.client_send = client_send

        self.leg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.LEG_ORDER = ["front_left", "front_right", "back_left", "back_right"]
        self.JOINT_ORDER = ["inner_shoulder", "outer_shoulder", "elbow"]

        self.leg_objects = dict()
        for leg in self.LEG_ORDER:
            if len(self.leg_objects) > 0:
                sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
                self.leg_box.append(sep)

            self.leg_objects[leg] = dict()

            b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            b.set_hexpand(True)
            self.leg_box.append(b)
            self.leg_objects[leg]["box"] = b

            for jnt in self.JOINT_ORDER:
                ident = f"{leg}_{jnt}"
                s = " ".join([p.capitalize() for p in ident.split("_")])
                label = Gtk.Label(label=s)
                label.set_margin_bottom(5)
                entry = Gtk.Entry()
                entry.set_editable(False)
                entry.set_text("42")
                entry.set_alignment(0.5) # center
                entry.set_margin_bottom(10)
                b.append(label)
                b.append(entry)
                self.leg_objects[leg][jnt] = {
                    "label": label,
                    "entry": entry,
                }

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

    def refresh(self):
        def update_servos(pkt):
            if pkt.op != "ACK":
                return None

            i = -1
            for leg in self.LEG_ORDER:
                for jnt in self.JOINT_ORDER:
                    i += 1
                    self.leg_objects[leg][jnt]["entry"].set_text(f"{pkt.contents[i]}")

        self.client_send(slipp.Packet("read_all_servo_positions"), on_recv_callback=update_servos)

    def on_enable_torque(self, btn):
        self.logfn("Telemetry", "enabling torque")
        self.client_send(slipp.Packet("enable_torque"))

    def on_disable_torque(self, btn):
        self.logfn("Telemetry", "disabling torque")
        self.client_send(slipp.Packet("enable_torque"))
