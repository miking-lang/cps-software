import os
import pathlib
import sys

from .. import slipp
from ..connection import ThreadedClientConnection

from ._gtk4 import GLib, Gtk, Gdk

from .boxes import CommandBox, ConnectionBox, LoggingBox, TelemetryBox

NAME = "Remote Ctrl GUI Client"
CURDIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

# Load CSS Data
css_provider = Gtk.CssProvider()
with open(CURDIR / "style.css", "rb") as f:
    css_provider.load_from_data(f.read())


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, application, *args, **kwargs):
        super().__init__(*args, application=application, **kwargs)
        self.__application = application
        self.set_default_size(800, 600)
        self.set_title(NAME)

        self.overlay = Gtk.Overlay()
        self.set_child(self.overlay)

        # Set CSS
        style_context = self.get_style_context()
        style_context.add_provider_for_display(
            Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.overlay.set_child(self.mainbox)

        self.topbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.mainbox.append(self.topbox)

        # TODO: For showing notifications
        #self.notifier = Gtk.Revealer()
        #self.notify_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        #self.notify_label = Gtk.Label(label="Test Overlay")
        #self.notify_box.append(self.notify_label)
        #self.notify_label.set_size_request(100, 40)
        #self.notifier.set_child(self.notify_box)
        #self.notifier.set_reveal_child(True)
        #self.overlay.add_overlay(self.notifier)

        self.send_button = Gtk.Button(label="Send (does nothing atm.)")
        self.send_button.connect("clicked", self.on_clicked_send)
        self.send_button.set_size_request(-1, 60)
        self.send_button.set_hexpand(True)
        self.send_button.add_css_class("white-button")
        self.topbox.append(self.send_button)

        self.quit_button = Gtk.Button(label="Quit")
        self.quit_button.connect("clicked", self.on_clicked_quit)
        self.quit_button.set_size_request(-1, 60)
        self.quit_button.set_hexpand(True)
        self.quit_button.add_css_class("red-button")
        self.topbox.append(self.quit_button)

        self.notebook = Gtk.Notebook()
        self.mainbox.append(self.notebook)

        # LOGGING
        self.logbox = LoggingBox()
        self.logbox_label = Gtk.Label(label="Log")
        self.logbox_label.set_size_request(100, 30)

        # CONNECTION
        self.connbox = ConnectionBox(
            logfn=self.logbox.add_log_entry,
        )
        self.connbox_label = Gtk.Label(label="Connection")
        self.connbox_label.set_size_request(100, 30)

        # TELEMETRY
        self.telemetry = TelemetryBox(
            logfn=self.logbox.add_log_entry,
            client_send=self.connbox.client_send,
        )
        self.telemetry_label = Gtk.Label(label="Telemetry")
        self.telemetry_label.set_size_request(100, 30)

        # COMMAND
        self.command = CommandBox(
            logfn=self.logbox.add_log_entry,
            client_send=self.connbox.client_send,
        )
        self.command_label = Gtk.Label(label="Command")
        self.command_label.set_size_request(100, 30)

        self.notebook.append_page(self.connbox, self.connbox_label)
        self.notebook.append_page(self.telemetry, self.telemetry_label)
        self.notebook.append_page(self.command, self.command_label)
        self.notebook.append_page(self.logbox, self.logbox_label)

        self.ongoing_timeouts = 0
        self.total_timeouts = 0
        self.start_timeout()

        self.__application.connect("shutdown", self.on_destroy)

        # By default, put focus on the connection box
        self.connbox.grab_focus()

    def on_destroy(self, app):
        #print("Destroying main window")
        if self.connbox.is_connected:
            self.connbox.disconnect()

    def on_clicked_quit(self, btn):
        self.__application.quit()

    def on_clicked_send(self, btn):
        #self.notify_label.set_text(f"Total timeouts: {self.total_timeouts}")
        pass

    def start_timeout(self):
        self.ongoing_timeouts += 1
        GLib.timeout_add(10, self.do_every_10ms)

    def do_every_10ms(self):
        """
        Things to do every 1000 ms
        """
        self.ongoing_timeouts -= 1
        self.total_timeouts += 1
        total_ms = self.total_timeouts * 10

        # Ping the server every 5 seconds
        if total_ms % 5000 == 0:
            self.connbox.client_send(slipp.Packet("PING"))

        # Every second, refresh the connbox
        if total_ms % 1000 == 0:
            self.connbox.refresh()

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
