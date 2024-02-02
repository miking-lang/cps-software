import sys

from ._gtk4 import GLib, Gtk, Gdk

from .. import slipp
from ..connection import ThreadedClientConnection

NAME = "Remote Ctrl GUI Client"

# Set up CSS provider
css_provider = Gtk.CssProvider()
css_provider.load_from_data(b"""
    .white-button {
        background-color: #f0f0f0;
        color: #0f0f0f;
    }
    .white-button:hover {
        background-color: #ffffff;
    }
    .red-button {
        background-color: #c02020;
        color: #f0f0f0;
    }
    .red-button:hover {
        background-color: #d01010;
        color: #0d0d0d;
    }
""")

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, application, *args, **kwargs):
        super().__init__(*args, application=application, **kwargs)
        self.__application = application
        self.set_default_size(800, 600)
        self.set_title(NAME)

        # Set CSS
        style_context = self.get_style_context()
        style_context.add_provider_for_display(
            Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.mainbox)

        self.topbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.mainbox.append(self.topbox)

        self.send_button = Gtk.Button(label="Send")
        self.send_button.connect("clicked", self.on_clicked_send)
        self.send_button.set_size_request(-1, 60)
        self.send_button.set_hexpand(True)
        self.send_button.add_css_class("white-button")
        self.topbox.append(self.send_button)

        self.connect_button = Gtk.Button(label="Connect")
        self.connect_button.connect("clicked", self.on_clicked_connect)
        self.connect_button.set_size_request(-1, 60)
        self.connect_button.set_hexpand(True)
        self.connect_button.add_css_class("white-button")
        self.topbox.append(self.connect_button)

        self.quit_button = Gtk.Button(label="Quit")
        self.quit_button.connect("clicked", self.on_clicked_quit)
        self.quit_button.set_size_request(-1, 60)
        self.quit_button.set_hexpand(True)
        self.quit_button.add_css_class("red-button")

        # Set the background color programmatically
        #color = Gdk.RGBA()
        #color.parse("blue")  # You can specify a color name or use hexadecimal values
        #self.quit_button.override_background_color(Gtk.StateFlags.NORMAL, color)

        self.topbox.append(self.quit_button)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Enter command")
        self.entry.connect("activate", self.on_entered_command)
        self.mainbox.append(self.entry)

        # Create a text view widget
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)  # Make it non-editable
        self.textview.set_cursor_visible(False)  # Hide the cursor

        # Create a scrolled window and add the text view to it
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(self.textview)
        scrolled_window.set_vexpand(True)

        # Create a text buffer for the text view
        textbuffer = self.textview.get_buffer()
        textbuffer.set_text("")

        self.mainbox.append(scrolled_window)

        self.text_entries = []

        self.timeouts = 0
        self.start_timeout()

        # Threaded client
        self.__client = None

        self.__application.connect("shutdown", self.on_destroy)

        # By default, put focus on the text field
        self.entry.grab_focus()

    def on_destroy(self, app):
        print("Destroying main window")
        self.client_disconnect()

    def on_clicked_quit(self, button):
        self.__application.quit()

    def client_connect(self):
        if self.__client is None:
            self.add_to_textbuffer("connecting")
            self.__client = ThreadedClientConnection(
                host="localhost", port=8372,
                on_packet=self.async_client_recv,
            )
            self.__client.start()

    def client_disconnect(self):
        if self.__client is not None:
            self.add_to_textbuffer("disconnecting")
            self.__client.stop()
            self.__client = None

    def async_client_recv(self, packet):
        """This function is GTK asynchronous, and is called when a packet is received."""
        GLib.idle_add(self.add_to_textbuffer, f"received packet: {str(packet)}")

    def client_send(self, packet):
        if self.__client is not None:
            self.add_to_textbuffer(f"sending packet: {str(packet)}")
            self.__client.send(packet)

    def on_clicked_send(self, button):
        text = self.entry.get_text()

        outpkt = slipp.Packet(op=text)
        self.client_send(outpkt)

        self.entry.set_text("")

    def on_clicked_connect(self, button):
        if self.__client is None:
            self.client_connect()
        else:
            self.client_disconnect()

    def on_entered_command(self, entry):
        text = self.entry.get_text()

        outpkt = slipp.Packet(op=text)
        self.client_send(outpkt)

        self.entry.set_text("")

    def add_to_textbuffer(self, text):
        self.text_entries.append(text)
        self.text_entries = self.text_entries[-100:]
        textbuffer = self.textview.get_buffer()
        textbuffer.set_text("\n".join(reversed(self.text_entries)))

    def start_timeout(self):
        GLib.timeout_add(1000, self.on_1s_timeout)  # Every 1000 milliseconds (1 second)

    def on_1s_timeout(self):
        self.timeouts += 1
        if self.timeouts % 5 == 0:
            self.client_send(slipp.Packet("PING", seq=f"{self.timeouts}"))

        # Start the timeout again
        self.start_timeout()


def run():
    def on_activate(app):
        win = MainWindow(application=app)
        win.present()

    app = Gtk.Application(application_id="org.miking.remote_ctrl.client")
    app.connect('activate', on_activate)
    GLib.set_application_name(NAME)
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
