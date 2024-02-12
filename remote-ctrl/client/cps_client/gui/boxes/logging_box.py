from datetime import datetime

from .._gtk4 import GLib, Gtk, Gdk, Pango

class LoggingBox(Gtk.Box):
    """
    A Logging box container for showing log messages.
    """
    def __init__(self, main_utils):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.set_margin_top(5)

        self.main_utils = main_utils

        # Create a Gtk.Scale widget
        self.textsize_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.textsize_label = Gtk.Label(label="<to be set>")
        self.textsize_label.set_size_request(90, -1)
        self.textsize_label.set_xalign(0.0)
        self.textsize_label.set_margin_start(10)
        self.textsize_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=Gtk.Adjustment(
                value=12,
                lower=8,
                upper=28,
                step_increment=1,
                page_increment=10,
                page_size=0,
            ),
        )
        self.textsize_scale.connect("value-changed", self.on_textsize_changed)
        self.textsize_scale.set_hexpand(True)
        self.textsize_scale.set_margin_end(10)
        self.textsize_box.append(self.textsize_label)
        self.textsize_box.append(self.textsize_scale)
        self.append(self.textsize_box)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_vexpand(True)
        self.append(self.scroll)

        self.textbuffer = Gtk.TextBuffer()
        self.textbuffer.set_text("")

        self.textview = Gtk.TextView(buffer=self.textbuffer)
        self.textview.set_editable(False)
        self.textview.set_cursor_visible(False)
        self.textview.set_monospace(True)
        self.scroll.set_child(self.textview)

        self.total_entries = 0
        self.max_len = 2**16
        self.bold_tag = self.textbuffer.create_tag("bold", weight=Pango.Weight.BOLD)

        # Common properties that all text should have
        self.common_tag = self.textbuffer.create_tag("common",
            size=10 * Pango.SCALE,
        )

        self.grey_tag = self.textbuffer.create_tag("grey_background")
        self.grey_tag.set_property("background", "#e0e0e0")

        # Initialize the text size
        self.on_textsize_changed(self.textsize_scale)

    def add_log_entry(self, title, msg):
        datetxt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        text_to_add = f"[{datetxt}] {title}: {msg}\n"
        self.textbuffer.insert_with_tags(self.textbuffer.get_start_iter(), text_to_add, self.common_tag)

        start_iter = self.textbuffer.get_iter_at_offset(0)
        end_iter = self.textbuffer.get_iter_at_offset(len(datetxt) + len(title) + 4)
        self.textbuffer.apply_tag(self.bold_tag, start_iter, end_iter)

        if self.total_entries % 2 == 0:
            end_iter = self.textbuffer.get_iter_at_offset(len(text_to_add))
            self.textbuffer.apply_tag(self.grey_tag, start_iter, end_iter)

        self.total_entries += 1
        self.refresh()

    def on_textsize_changed(self, scale):
        new_font_size = int(scale.get_value())
        self.common_tag.set_property("size", new_font_size * Pango.SCALE)
        self.textsize_label.set_text(f"Text Size: {new_font_size}")

    def refresh(self):
        if self.textbuffer.get_char_count() > self.max_len:
            # Remove too old text
            start_iter = self.textbuffer.get_iter_at_offset(int(self.max_len * 0.9))
            end_iter = self.textbuffer.get_end_iter()
            self.textbuffer.delete(start_iter, end_iter)
