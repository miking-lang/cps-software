from .._gtk4 import GLib, Gtk, Gdk

from ...connection import ThreadedClientConnection
from ...import slipp

class ConnectionBox(Gtk.Box):
    """
    A Connection box container for handling connection to server.
    """
    def __init__(self, main_utils):
        """
        main_utils : Class with shared utilities from the MainWindow.
        """
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.set_margin_top(5)

        self.client = None
        self.main_utils = main_utils

        self.left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.left_col.set_margin_start(5)
        self.right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.right_col.set_margin_end(5)

        self.append(self.left_col)
        self.append(self.right_col)

        self.left_col.set_hexpand(True)
        self.right_col.set_hexpand(True)

        self.entry_host = self.main_utils.cache.CacheEntry("HOST", default="localhost")
        self.entry_host.set_placeholder_text("Hostname")
        self.left_col.append(self.entry_host)

        self.entry_port = self.main_utils.cache.CacheEntry("PORT", default="8372")
        self.entry_port.set_placeholder_text("Port")
        self.left_col.append(self.entry_port)

        self.text_status = Gtk.TextView()
        self.text_status.set_editable(False)
        self.text_status.set_cursor_visible(False)
        self.text_status.set_vexpand(True)
        self.text_status.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.set_status_text("Status")
        self.left_col.append(self.text_status)

        self.btn_connect = Gtk.Button(label="Connect")
        self.btn_connect.connect("clicked", self.on_click_btn_connect)
        self.btn_connect.set_size_request(-1, 60)
        self.btn_connect.add_css_class("white-button")
        self.right_col.append(self.btn_connect)

        self.connectbox_disconnect_button = Gtk.Button(label="Disconnect")
        self.connectbox_disconnect_button.connect("clicked", self.on_click_btn_disconnect)
        self.connectbox_disconnect_button.set_size_request(-1, 60)
        self.connectbox_disconnect_button.add_css_class("red-button")
        self.right_col.append(self.connectbox_disconnect_button)


        def send_cmd(cmd, args=[]):
            self.client_send(slipp.Packet(cmd, contents={"args": args}),
                on_recv_callback=lambda pkt: self.set_status_text(str(pkt.contents))
            )
        CMDS = [
            ("LSCONN", lambda btn: send_cmd("LSCONN")),
            ("LSCMD", lambda btn: send_cmd("LSCMD")),
            #("read_all_servo_goalplans", lambda btn: send_cmd("read_all_servo_goalplans")),
            #("read_all_servo_registers (PRESENT_POSITION)", lambda btn: send_cmd("read_all_servo_registers", args=["PRESENT_POSITION", "PRESENT_POSITION"])),
            #("read FR_INNER_SHOULDER", lambda btn: send_cmd("read_single_servo_position", args=["FR_INNER_SHOULDER"])),
            #("read FR_OUTER_SHOULDER", lambda btn: send_cmd("read_single_servo_position", args=["FR_OUTER_SHOULDER"])),
            #("read FR_ELBOW", lambda btn: send_cmd("read_single_servo_position", args=["FR_ELBOW"])),
            #("read FL_INNER_SHOULDER", lambda btn: send_cmd("read_single_servo_position", args=["FL_INNER_SHOULDER"])),
            #("read FL_OUTER_SHOULDER", lambda btn: send_cmd("read_single_servo_position", args=["FL_OUTER_SHOULDER"])),
            #("read FL_ELBOW", lambda btn: send_cmd("read_single_servo_position", args=["FL_ELBOW"])),
            #("read BR_INNER_SHOULDER", lambda btn: send_cmd("read_single_servo_position", args=["BR_INNER_SHOULDER"])),
            #("read BR_OUTER_SHOULDER", lambda btn: send_cmd("read_single_servo_position", args=["BR_OUTER_SHOULDER"])),
            #("read BR_ELBOW", lambda btn: send_cmd("read_single_servo_position", args=["BR_ELBOW"])),
            #("read BL_INNER_SHOULDER", lambda btn: send_cmd("read_single_servo_position", args=["BL_INNER_SHOULDER"])),
            #("read BL_OUTER_SHOULDER", lambda btn: send_cmd("read_single_servo_position", args=["BL_OUTER_SHOULDER"])),
            #("read BL_ELBOW", lambda btn: send_cmd("read_single_servo_position", args=["BL_ELBOW"])),
        ]

        for (cmd, cmdfn) in CMDS:
            btn = Gtk.Button(label=cmd)
            btn.connect("clicked", cmdfn)
            btn.set_size_request(-1, 40)
            self.right_col.append(btn)

    def set_status_text(self, msg):
        textbuffer = self.text_status.get_buffer()
        textbuffer.set_text(msg)

    @property
    def is_connected(self):
        if self.client is None:
            return False
        return self.client.is_active

    def refresh(self):
        """Refreshes the GUI for this box."""
        if self.client is not None and self.client.failed:
            self.main_utils.notify("Connection failed")
            self.set_status_text(self.client.fail_msg)
            self.client = None

        if self.client is None:
            self.btn_connect.set_label("Connect")
            self.btn_connect.remove_css_class("lightgreen-button")
            self.btn_connect.add_css_class("white-button")
        if self.client is not None:
            self.client.check_timeouts()

    def set_as_connected(self, pkt):
        self.main_utils.log("Status", "connected")
        self.btn_connect.set_label("Connected")
        self.btn_connect.remove_css_class("white-button")
        self.btn_connect.add_css_class("lightgreen-button")
        self.set_status_text("Connected")
        self.main_utils.notify("Connected", success=True)

    def connect(self):
        host=self.entry_host.get_text()
        port=self.entry_port.get_text()
        self.main_utils.cache.set("host", str(host))
        self.main_utils.cache.set("port", str(port))
        self.set_status_text(f"Connecting to {host}:{port}...")
        try:
            self.client = ThreadedClientConnection(
                host=str(host), port=int(port),
                logfn=lambda title, msg: GLib.idle_add(self.main_utils.log, title, msg)
            )
            self.client.start()
            self.client_send(slipp.Packet("PING"), on_recv_callback=self.set_as_connected)
        except Exception as e:
            self.main_utils.notify("Connection failed")
            self.set_status_text(str(e))
            self.client = None

    def disconnect(self):
        if self.client is not None:
            self.set_status_text("Disonnecting...")
            self.client.stop()
            self.client = None

    def on_click_btn_connect(self, btn):
        if self.is_connected:
            self.set_status_text("Already connected...")
        else:
            self.connect()

    def on_click_btn_disconnect(self, btn):
        if not self.is_connected:
            self.set_status_text("Not connected, cannot disconnect...")
        else:
            self.disconnect()

    def client_send(self, packet,
                    on_recv_callback = None,
                    on_timeout_callback = None,
                    ttl : float = 5.0):
        if self.client is not None:
            try:
                # Make sure that callbacks are async wrapped
                on_recv = None
                on_timeout = None
                if on_recv_callback is not None:
                    on_recv = lambda pkt: GLib.idle_add(on_recv_callback, pkt)
                if on_timeout_callback is not None:
                    on_timeout = lambda: GLib.idle_add(on_timeout_callback)
                self.client.send(packet,
                                 on_recv_callback=on_recv,
                                 on_timeout_callback=on_timeout,
                                 ttl=ttl)
            except Exception as e:
                self.set_status_text(str(e))
                return False
            else:
                return True
        else:
            return False
