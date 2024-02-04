from datetime import datetime

from .._gtk4 import GLib, Gtk, Gdk, Pango

class LoggingBox(Gtk.Box):
    """
    A Logging box container for showing log messages.
    """
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        # Create a Gtk.Scale widget
        self.textsize_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.textsize_label = Gtk.Label(label="<to be set>")
        self.textsize_label.set_size_request(100, -1)
        self.textsize_label.set_justify(Gtk.Justification.LEFT)
        self.textsize_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL,
            adjustment=Gtk.Adjustment(
                value=16,
                lower=10,
                upper=28,
                step_increment=1,
                page_increment=10,
                page_size=0,
            ),
        )
        self.textsize_scale.connect("value-changed", self.on_textsize_changed)
        self.textsize_scale.set_hexpand(True)
        self.textsize_box.append(self.textsize_label)
        self.textsize_box.append(self.textsize_scale)
        self.append(self.textsize_box)
        # Initialize the text size
        self.on_textsize_changed(self.textsize_scale)

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
        self.textview.add_css_class("logbox-textview")
        self.scroll.set_child(self.textview)

        self.total_entries = 0
        self.max_len = 2**14
        self.bold_tag = self.textbuffer.create_tag("bold", weight=Pango.Weight.BOLD)

        self.grey_tag = self.textbuffer.create_tag("grey_background")
        self.grey_tag.set_property("background", "#e0e0e0")

    def add_log_entry(self, title, msg):
        datetxt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        text_to_add = f"[{datetxt}] {title}: {msg}\n"
        self.textbuffer.insert(self.textbuffer.get_start_iter(), text_to_add)

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
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(f"""
            .logbox-textview {{ font-size: {new_font_size}px; }}
        """.encode('utf-8'))
        self.textsize_label.set_text(f"Text Size: {new_font_size}")
        self.textsize_label.set_justify(Gtk.Justification.LEFT)

        context = self.get_style_context()
        context.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def refresh(self):
        if self.textbuffer.get_char_count() > self.max_len:
            # Remove too old text
            start_iter = self.textbuffer.get_iter_at_offset(self.max_len)
            end_iter = self.textbuffer.get_end_iter()
            self.textbuffer.delete(start_iter, end_iter)
