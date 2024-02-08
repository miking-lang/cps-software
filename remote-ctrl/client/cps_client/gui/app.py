import os
import pathlib
import sys

from typing import Callable, Optional

from .. import slipp
from ..connection import ThreadedClientConnection

from ._gtk4 import GLib, Gtk, Gdk
from .cache import JSONParameterCache

from .boxes import ControlBox, ConnectionBox, LoggingBox, TelemetryBox

NAME = "Remote Ctrl GUI Client"
CURDIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

# Load CSS Data
css_provider = Gtk.CssProvider()
with open(CURDIR / "style.css", "rb") as f:
    css_provider.load_from_data(f.read())


class MainWindow(Gtk.ApplicationWindow):
    class MainUtils:
        """Main utils class with things that everyone should be able to access."""
        def __init__(self):
            """
            log : str -> str -> ()
            client_send : Packet -> Option(Packet -> ()) -> Option(() -> ()) -> Option(float)
            cache : JSONParameterCache
            notify : str -> Option(bool) -> ()
            """
            self.log = None
            self.client_send  = None
            self.cache = None
            self.notify = None

    def __init__(self, application, *args, **kwargs):
        super().__init__(*args, application=application, **kwargs)
        self.__application = application
        self.__cache = JSONParameterCache(cache_name=application.get_application_id())
        self.set_default_size(800, 600)
        self.set_title(NAME)

        self.overlay = Gtk.Overlay()
        self.set_child(self.overlay)

        self.__main_utils = MainWindow.MainUtils()
        self.__main_utils.cache = self.__cache
        self.__main_utils.notify = self.on_notify

        # Set CSS
        style_context = self.get_style_context()
        style_context.add_provider_for_display(
            Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.overlay.set_child(self.mainbox)

        self.topbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.mainbox.append(self.topbox)

        # For showing notifications with on_notify
        self.notifier = Gtk.Revealer()
        self.notify_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.notify_label = Gtk.Label(label="<NOTIFICATION>")
        self.notify_label.set_size_request(100, 40)
        self.notify_label.add_css_class("red-button")
        self.notify_box.append(self.notify_label)
        self.notify_box.set_size_request(100, 40)
        self.notifier.set_child(self.notify_box)
        self.notifier.set_reveal_child(False)
        self.notifier.set_can_target(False) # Make this click-through
        self.notifier.set_size_request(100, 40)
        self.notifier.set_transition_duration(150)
        self.notifier.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.notifier_target_hide_ms = -1 # Timeout ms for when to hide the notification
        self.overlay.add_overlay(self.notifier)

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
        self.logbox = LoggingBox(self.__main_utils)
        self.logbox_label = Gtk.Label(label="Log")
        self.logbox_label.set_size_request(100, 30)

        # Add logging functions
        self.__main_utils.log = self.logbox.add_log_entry

        # CONNECTION
        self.connbox = ConnectionBox(self.__main_utils)
        self.connbox_label = Gtk.Label(label="Connection")
        self.connbox_label.set_size_request(100, 30)

        # Add the client_send util
        self.__main_utils.client_send = self.connbox.client_send

        # TELEMETRY
        self.telemetry = TelemetryBox(self.__main_utils)
        self.telemetry_label = Gtk.Label(label="Telemetry")
        self.telemetry_label.set_size_request(100, 30)

        # CONTROL
        self.control = ControlBox(self.__main_utils)
        self.control_label = Gtk.Label(label="Control")
        self.control_label.set_size_request(100, 30)

        self.notebook.append_page(self.connbox, self.connbox_label)
        self.notebook.append_page(self.telemetry, self.telemetry_label)
        self.notebook.append_page(self.control, self.control_label)
        self.notebook.append_page(self.logbox, self.logbox_label)

        self.ongoing_timeouts = 0
        self.total_timeouts = 0
        self.timeout_period_ms = 10
        self.total_timeout_ms = 0
        self.start_timeout()

        self.__application.connect("shutdown", self.on_destroy)

        # By default, put focus on the connection box
        self.connbox.grab_focus()

    def on_destroy(self, app):
        #print("Destroying main window")
        if self.connbox.is_connected:
            self.connbox.disconnect()
        
        self.__cache.writeback()

    def on_clicked_quit(self, btn):
        self.__application.quit()

    def on_clicked_send(self, btn):
        #self.notify_label.set_text(f"Total timeouts: {self.total_timeouts}")
        pass

    def on_notify(self, text, success=False):
        self.notifier.set_reveal_child(False)
        self.notify_label.set_text(text)
        self.notifier_target_hide_ms = self.total_timeout_ms + 2000 + 25*len(text)
        if success:
            self.notify_label.add_css_class("lightgreen-button")
            self.notify_label.remove_css_class("red-button")
        else:
            self.notify_label.add_css_class("red-button")
            self.notify_label.remove_css_class("lightgreen-button")
        self.notifier.set_reveal_child(True)

    def start_timeout(self):
        self.ongoing_timeouts += 1
        GLib.timeout_add(self.timeout_period_ms, self.do_every_10ms)

    def do_every_10ms(self):
        """
        Things to do every 1000 ms
        """
        self.ongoing_timeouts -= 1
        self.total_timeouts += 1
        self.total_timeout_ms += self.timeout_period_ms

        # Ping the server every 10 seconds
        if self.total_timeout_ms % 10000 == 0:
            self.connbox.client_send(slipp.Packet("PING"))

        # Every second, refresh the connbox
        if self.total_timeout_ms % 1000 == 0:
            self.connbox.refresh()
        
        # Perform cache writeback
        if self.total_timeout_ms % 5000 == 0:
            self.__cache.writeback()

        if self.total_timeout_ms >= self.notifier_target_hide_ms:
            self.notifier.set_reveal_child(False)

        # Testing for reveal of child.
        #if total_ms % 2000 == 0:
        #    self.notifier.set_reveal_child(bool(total_ms % 6000 == 0))

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
