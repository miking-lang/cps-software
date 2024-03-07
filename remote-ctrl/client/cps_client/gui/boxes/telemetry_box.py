import itertools

from .._gtk4 import GLib, Gtk, Gdk, Pango
from ..gui_types import Refresher

from ... import slipp, utils


class TelemetryBox(Refresher, Gtk.Box):
    """
    A Telemetry box for reading telemetry from the spider.
    """
    def __init__(self, main_utils):
        """
        main_utils : Class with shared utilities from the MainWindow.
        """
        # Initialize this as a refreshing object
        Refresher.__init__(self, refresh_rate_ms=1000)

        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.set_margin_top(5)

        self.main_utils = main_utils
        self.waiting_for_tm = False
        self.waiting_for_rom_tm = False

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
        self.servo_order = self.main_utils.cache.get("SERVO_ORDER")
        self.synced_servo_order = False
        def set_servo_order(v):
            self.servo_order = v
        self.main_utils.cache.register_callback("SERVO_ORDER", set_servo_order)

        self.entry_attrs = Pango.AttrList()
        self.entry_attrs.insert(Pango.AttrFontDesc.new(Pango.FontDescription("Monospace")))

        self.small_mono_attrs = Pango.AttrList()
        self.small_mono_attrs.insert(Pango.AttrFontDesc.new(Pango.FontDescription("Monospace")))
        self.small_mono_attrs.insert(Pango.attr_size_new(10 * Pango.SCALE))

        self.title_attrs = Pango.AttrList()
        self.title_attrs.insert(Pango.attr_weight_new(Pango.Weight.BOLD))

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
            leg_label.set_attributes(self.title_attrs)
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
                entry.set_attributes(self.entry_attrs)
                entry.set_alignment(0.5) # center
                entry.set_margin_bottom(10)
                b.append(button)
                b.append(entry)
                self.leg_objects[leg][jnt] = {
                    "button": button,
                    "entry": entry,
                    "raw_values": {},
                    "servo_id": servo_id,
                    "has_error": False,
                }
                self.servo_id_lookup[servo_id] = (leg, jnt)

        # Detailed status shown for individual legs
        self.left_col.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        self.joint_status_scroll = Gtk.ScrolledWindow()
        self.joint_status_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.joint_status_scroll.set_vexpand(True)
        self.left_col.append(self.joint_status_scroll)

        self.joint_status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.joint_status_scroll.set_child(self.joint_status_box)
        self.joint_status_header = Gtk.Label(label="NO DATA SHOWN HERE YET")
        self.joint_status_header.set_attributes(self.title_attrs)
        self.joint_status_box.append(self.joint_status_header)

        self.joint_status_colbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.joint_status_box.append(self.joint_status_colbox)

        self.joint_status_cols = []
        for i in range(5):
            if i > 0:
                self.joint_status_colbox.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
            colbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            self.joint_status_colbox.append(colbox)
            self.joint_status_cols.append(colbox)

        self.joint_status_active_joint = self.servo_order[0]
        self.joint_status_fields = dict()

        # Add toggle for enabling/disabling collection
        self.tm_collect_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.tm_collect_box.set_margin_start(5)
        self.tm_collect_box.set_margin_end(5)
        self.right_col.append(self.tm_collect_box)
        self.tm_collect_label = Gtk.Label(label="Enable Collection")
        self.tm_collect_switch = Gtk.Switch()
        self.tm_collect_switch.set_active(False)
        self.tm_collect_box.append(self.tm_collect_label)
        self.tm_collect_box.append(self.tm_collect_switch)

        # Add toggle for which metric to display positions as
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

        # Buttons for servo control
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
        self.entry_torque_status.set_attributes(self.entry_attrs)
        self.entry_torque_status.set_size_request(100, 30)
        self.right_col.append(self.entry_torque_status)

        self.btn_reboot = Gtk.Button(label="Reboot")
        self.btn_reboot.connect("clicked", self.on_reboot)
        self.btn_reboot.set_margin_top(10)
        self.btn_reboot.set_size_request(100, 30)
        self.right_col.append(self.btn_reboot)

        # Duration and acceleration info
        self.status_duration_label = Gtk.Label(label="Duration")
        self.status_duration_label.set_margin_top(10)
        self.right_col.append(self.status_duration_label)

        self.status_duration_entry = Gtk.Entry()
        self.status_duration_entry.set_text("<NO STATUS YET>")
        self.status_duration_entry.set_editable(False)
        self.status_duration_entry.set_attributes(self.entry_attrs)
        self.status_duration_entry.set_size_request(100, 30)
        self.right_col.append(self.status_duration_entry)

        self.status_acceleration_label = Gtk.Label(label="Acceleration")
        self.status_acceleration_label.set_margin_top(10)
        self.right_col.append(self.status_acceleration_label)

        self.status_acceleration_entry = Gtk.Entry()
        self.status_acceleration_entry.set_text("<NO STATUS YET>")
        self.status_acceleration_entry.set_editable(False)
        self.status_acceleration_entry.set_attributes(self.entry_attrs)
        self.status_acceleration_entry.set_size_request(100, 30)
        self.right_col.append(self.status_acceleration_entry)

        self.status_servos_setup_label = Gtk.Label(label="Servos Set Up")
        self.status_servos_setup_label.set_margin_top(10)
        self.right_col.append(self.status_servos_setup_label)

        self.status_servos_setup_entry = Gtk.Entry()
        self.status_servos_setup_entry.set_text("<NO STATUS YET>")
        self.status_servos_setup_entry.set_editable(False)
        self.status_servos_setup_entry.set_attributes(self.entry_attrs)
        self.status_servos_setup_entry.set_size_request(100, 30)
        self.right_col.append(self.status_servos_setup_entry)

        # Accelerometer and Gyro info
        self.coord_order = ["x", "y", "z"]
        def create_labelled_entry(name):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            label = Gtk.Label(label=name)
            label.set_attributes(self.title_attrs)
            label.set_margin_start(5)
            entry = Gtk.Entry()
            entry.set_text("<NO VALUE YET>")
            entry.set_editable(False)
            entry.set_attributes(self.entry_attrs)
            entry.set_max_width_chars(14)
            box.append(label)
            box.append(entry)
            return {"box": box, "label": label, "entry": entry}

        self.status_accelerometer_label = Gtk.Label(label="Accelerometer")
        self.status_accelerometer_label.set_margin_top(10)
        self.status_accelerometer_label.set_attributes(self.title_attrs)
        self.right_col.append(self.status_accelerometer_label)
        self.status_accelerometer_coords = {
            coord: create_labelled_entry(coord.upper())
            for coord in self.coord_order
        }
        for coord in self.coord_order:
            self.right_col.append(self.status_accelerometer_coords[coord]["box"])

        self.status_gyro_label = Gtk.Label(label="Gyroscope")
        self.status_gyro_label.set_margin_top(10)
        self.status_gyro_label.set_attributes(self.title_attrs)
        self.right_col.append(self.status_gyro_label)
        self.status_gyro_coords = {
            coord: create_labelled_entry(coord.upper())
            for coord in self.coord_order
        }
        for coord in self.coord_order:
            self.right_col.append(self.status_gyro_coords[coord]["box"])

        self.update_leg_texts()
        self.start_refresh()

    def update_leg_texts(self):
        for leg, jnt in itertools.product(self.LEG_ORDER, self.JOINT_ORDER):
            legobj = self.leg_objects[leg][jnt]

            raw_v = legobj["raw_values"].get("PRESENT_POSITION")
            servo_id = legobj["servo_id"]
            if raw_v is not None:
                if self.metric_check_degrees.get_active():
                    v = utils.dynamixel.raw_to_degrees(int(raw_v), key=servo_id)
                    legobj["entry"].set_text(f"{float(v):.04f}")
                elif self.metric_check_radians.get_active():
                    v = utils.dynamixel.raw_to_radians(int(raw_v), key=servo_id)
                    legobj["entry"].set_text(f"{float(v):.04f}")
                else:
                    legobj["entry"].set_text(f"{int(raw_v)}")
            else:
                legobj["entry"].set_text(f"{servo_id}")
            # Set button color (red if error, otherwise white)
            legobj["button"].remove_css_class("lightblue-button")
            hw_error = legobj["raw_values"].get("HARDWARE_ERROR_STATUS", 0)
            if hw_error != 0:
                legobj["button"].add_css_class("red-button")
                if not legobj["has_error"]:
                    self.main_utils.notify(f"Hardware error {hw_error} on {servo_id}")
                    legobj["has_error"] = True
            else:
                legobj["button"].remove_css_class("red-button")
                legobj["button"].add_css_class("white-button")
                legobj["has_error"] = False

        (leg, jnt) = self.servo_id_lookup[self.joint_status_active_joint]
        self.joint_status_header.set_text(str(self.joint_status_active_joint))
        for k, (label, entry) in self.joint_status_fields.items():
            entry.set_text("NO DATA")
        for k, v in sorted(self.leg_objects[leg][jnt]["raw_values"].items(), key=lambda e: e[0]):
            if k not in self.joint_status_fields:
                label = Gtk.Label(label=k)
                label.set_attributes(self.small_mono_attrs)
                label.set_margin_top(10)
                entry = Gtk.Entry()
                entry.set_editable(False)
                entry.set_alignment(0.5) # center
                entry.set_attributes(self.entry_attrs)
                colidx = len(self.joint_status_fields) % len(self.joint_status_cols)
                self.joint_status_cols[colidx].append(label)
                self.joint_status_cols[colidx].append(entry)
                self.joint_status_fields[k] = (label, entry)

            (label, entry) = self.joint_status_fields[k]
            entry.set_text(str(v))
        #status_lines = [f"[{self.joint_status_active_joint}]"]
        #    status_lines.append(f"{k}: {v}")
        #self.joint_status_text.set_text("\n".join(status_lines))
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
            self.main_utils.cache.set("SERVO_ORDER", pkt.contents["data"])
            self.synced_servo_order = True

        if not self.synced_servo_order:
            self.main_utils.client_send(slipp.Packet("get_servos"), on_recv_callback=update_servo_order)

        if self.tm_collect_switch.get_active():
            self.main_utils.client_send(
                slipp.Packet("get_duration"),
                on_recv_callback=lambda pkt: self.status_duration_entry.set_text(str(pkt.contents["data"])))

        if self.tm_collect_switch.get_active():
            self.main_utils.client_send(
                slipp.Packet("get_acceleration"),
                on_recv_callback=lambda pkt: self.status_acceleration_entry.set_text(str(pkt.contents["data"])),
            )

        if self.tm_collect_switch.get_active():
            self.main_utils.client_send(
                slipp.Packet("get_position_control_configured"),
                on_recv_callback=lambda pkt: self.status_servos_setup_entry.set_text(any(pkt.contents["data"])),
            )

        def update_accelerometer(pkt):
            for i, coord in enumerate(self.coord_order):
                self.status_accelerometer_coords[coord]["entry"].set_text(str(pkt.contents["data"][i]))

        if self.tm_collect_switch.get_active():
            self.main_utils.client_send(
                slipp.Packet("read_accel"),
                on_recv_callback=update_accelerometer,
            )

        def update_gyro(pkt):
            for i, coord in enumerate(self.coord_order):
                self.status_gyro_coords[coord]["entry"].set_text(str(pkt.contents["data"][i]))

        if self.tm_collect_switch.get_active():
            self.main_utils.client_send(
                slipp.Packet("read_gyro"),
                on_recv_callback=update_gyro,
            )

        def update_values(pkt):
            self.waiting_for_tm = False
            if pkt.op != "ACK":
                return None
            for i, servo_id in enumerate(self.servo_order):
                leg, jnt = self.servo_id_lookup[servo_id]
                for k, v in pkt.contents["data"].items():
                    self.leg_objects[leg][jnt]["raw_values"][k] = v[i]
            self.update_leg_texts()

            torque_txt = "disabled"
            if min(pkt.contents["data"]["TORQUE_ENABLE"]) == 1:
                torque_txt = "enabled"
            self.entry_torque_status.set_text(torque_txt)

        def tm_timeout():
            self.waiting_for_tm = False

        if not self.waiting_for_tm:
            if self.tm_collect_switch.get_active():
                ok = self.main_utils.client_send(
                    slipp.Packet("read_all_servos_RAM"),
                    on_recv_callback=update_values,
                    on_timeout_callback=tm_timeout,
                    ttl=2.0)
                if ok:
                    self.waiting_for_tm = True

        def rom_update_values(pkt):
            self.waiting_for_rom_tm = False
            if pkt.op != "ACK":
                return None
            for i, servo_id in enumerate(self.servo_order):
                leg, jnt = self.servo_id_lookup[servo_id]
                for k, v in pkt.contents["data"].items():
                    self.leg_objects[leg][jnt]["raw_values"][k] = v[i]
            self.update_leg_texts()

        def rom_tm_timeout():
            self.waiting_for_rom_tm = False

        if not self.waiting_for_rom_tm:
            if self.tm_collect_switch.get_active():
                ok = self.main_utils.client_send(
                    slipp.Packet("read_all_servo_registers", contents={"args": ["MODEL_NUMBER", "SHUTDOWN"]}),
                    on_recv_callback=rom_update_values,
                    on_timeout_callback=rom_tm_timeout,
                    ttl=2.0)
                if ok:
                    self.waiting_for_rom_tm = True

    def on_enable_torque(self, btn):
        self.main_utils.log("Telemetry", "enabling torque")
        self.main_utils.client_send(slipp.Packet("enable_torque"))

    def on_disable_torque(self, btn):
        self.main_utils.log("Telemetry", "disabling torque")
        self.main_utils.client_send(slipp.Packet("disable_torque"))

    def on_reboot(self, btn):
        self.main_utils.log("Telemetry", "rebooting")
        self.main_utils.client_send(slipp.Packet("reboot_all_servos"))
