"""
Pseudo module to ensure that everyone gets the same GTK.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk, Gdk, Pango

from typing import Tuple

def pango_attrlist(**kwargs):
    # name -> (function, expected type, brief description)
    PANGO_ATTRS = {
        "background": (Pango.attr_background_new, Tuple[float, float, float], "(red, green, blue)"),
        "textsize": (lambda v: Pango.attr_size_new(v * Pango.SCALE), int, "text size"),
    }

    al = Pango.AttrList()

    for attr_key, arguments in kwargs.items():
        if not isinstance(arguments, tuple):
            arguments = (arguments,)
        attr = PANGO_ATTRS[attr_key][0](*arguments)
        al.insert(attr)

    return al
