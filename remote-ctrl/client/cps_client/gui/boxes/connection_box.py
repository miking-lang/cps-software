from .._gtk4 import GLib, Gtk, Gdk

from ...connection import ThreadedClientConnection
from ...import slipp

class ConnectionBox(Gtk.Box):
    """
    A Connection box container for handling connection to server.
    """
    def __init__(self, logfn):
        """
        logfn : Callback logging
        """
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)

        self.client = None
        self.logfn = logfn

        self.left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.append(self.left_col)
        self.append(self.right_col)

        self.left_col.set_hexpand(True)
        self.right_col.set_hexpand(True)

        self.entry_host = Gtk.Entry()
        self.entry_host.set_placeholder_text("Hostname")
        self.entry_host.set_text("localhost")
        self.left_col.append(self.entry_host)

        self.entry_port = Gtk.Entry()
        self.entry_port.set_placeholder_text("Port")
        self.entry_port.set_text("8372")
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

        def on_lsconn(btn):
            self.client_send(slipp.Packet("LSCONN"),
                on_recv_callback=lambda pkt: self.set_status_text(str(pkt.contents))
            )
        self.btn_lsconn = Gtk.Button(label="LSCONN")
        self.btn_lsconn.connect("clicked", on_lsconn)
        self.btn_lsconn.set_size_request(-1, 40)
        self.btn_lsconn.set_margin_top(5)
        self.right_col.append(self.btn_lsconn)

        def on_lscmd(btn):
            self.client_send(slipp.Packet("LSCMD"),
                on_recv_callback=lambda pkt: self.set_status_text(str(pkt.contents))
            )
        self.btn_lscmd = Gtk.Button(label="LSCMD")
        self.btn_lscmd.connect("clicked", on_lscmd)
        self.btn_lscmd.set_size_request(-1, 40)
        self.btn_lscmd.set_margin_top(5)
        self.right_col.append(self.btn_lscmd)

    def set_status_text(self, msg):
        textbuffer = self.text_status.get_buffer()
        textbuffer.set_text(msg)

    @property
    def is_connected(self):
        return bool(self.client is not None)

    def refresh(self):
        """Refreshes the GUI for this box."""
        if self.client is None:
            self.btn_connect.set_label("Connect")
            self.btn_connect.remove_css_class("lightgreen-button")
            self.btn_connect.add_css_class("white-button")

    def set_as_connected(self, pkt):
        self.logfn("Status", "connected")
        self.btn_connect.set_label("Connected")
        self.btn_connect.remove_css_class("white-button")
        self.btn_connect.add_css_class("lightgreen-button")

    def connect(self):
        host=self.entry_host.get_text()
        port=self.entry_port.get_text()
        self.set_status_text(f"Connecting to {host}:{port}...")
        try:
            self.client = ThreadedClientConnection(
                host=str(host), port=int(port),
                logfn=lambda title, msg: GLib.idle_add(self.logfn, title, msg)
            )
            self.client.start()
            self.client_send(slipp.Packet("PING"), on_recv_callback=self.set_as_connected)
        except Exception as e:
            self.set_status_text(str(e))
            self.client = None

    def disconnect(self):
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
                    on_timeout_callback = None):
        if self.is_connected:
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
                                 on_timeout_callback=on_timeout)
            except Exception as e:
                self.set_status_text(str(e))