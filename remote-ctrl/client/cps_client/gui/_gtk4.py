"""
Pseudo module to ensure that everyone gets the same GTK.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk, Gdk
