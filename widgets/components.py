"""Reusable Tkinter widgets used across every screen.

Keeping the widgets here means each screen only describes *what* it shows,
never *how* a button, card or form field is drawn.
"""

import tkinter as tk
from tkinter import ttk

from config import AVATAR_COLORS, STATUS_STYLES, Colors, font
from utils.helpers import avatar_color_for, initials

try:  # Pillow ships with matplotlib, so it is normally available.
    from PIL import Image, ImageDraw, ImageTk
except ImportError:  # pragma: no cover - fallback to initials only
    Image = ImageDraw = ImageTk = None


def _has_focus(widget: tk.Misc) -> bool:
    """True if ``widget`` currently has keyboard focus (safe for combobox popups)."""
    try:
        return widget.focus_get() is widget
    except KeyError:
        return False


# ----------------------------------------------------------------------------
# Global styling
# ----------------------------------------------------------------------------
def setup_styles(root: tk.Misc) -> None:
    """Configure ttk widgets (combobox, scrollbar) to match the Figma design."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "App.TCombobox", fieldbackground=Colors.SURFACE, background=Colors.SURFACE,
        foreground=Colors.TEXT, bordercolor=Colors.BORDER, lightcolor=Colors.SURFACE,
        darkcolor=Colors.SURFACE, arrowcolor=Colors.TEXT_MUTED, padding=6,
    )
    style.map(
        "App.TCombobox",
        fieldbackground=[("readonly", Colors.SURFACE)],
        foreground=[("readonly", Colors.TEXT)],
        bordercolor=[("focus", Colors.PRIMARY)],
    )
    style.configure(
        "Vertical.TScrollbar", background=Colors.BORDER, troughcolor=Colors.BG,
        bordercolor=Colors.BG, arrowcolor=Colors.TEXT_MUTED, relief="flat",
    )
    root.option_add("*TCombobox*Listbox.font", font(10))
    root.option_add("*TCombobox*Listbox.background", Colors.SURFACE)
    root.option_add("*TCombobox*Listbox.foreground", Colors.TEXT)


def bind_mousewheel(root: tk.Misc) -> None:
    """Route mouse wheel and precision touchpad events to the hovered page."""

    def on_wheel(event):
        widget = event.widget
        while widget is not None:
            if isinstance(widget, ScrollableFrame):
                break
            widget = getattr(widget, "master", None)
        if widget is None:
            widget = root.winfo_containing(event.x_root, event.y_root)
            while widget is not None and not isinstance(widget, ScrollableFrame):
                widget = getattr(widget, "master", None)
        if widget is None:
            return

        if getattr(event, "num", None) == 4:
            widget.scroll_units(-2)
        elif getattr(event, "num", None) == 5:
            widget.scroll_units(2)
        else:
            widget.scroll_wheel_delta(event.delta)
        return "break"

    root.bind_all("<MouseWheel>", on_wheel)  # Windows / macOS
    root.bind_all("<Button-4>", on_wheel)  # Linux scroll up
    root.bind_all("<Button-5>", on_wheel)  # Linux scroll down


# ----------------------------------------------------------------------------
# Buttons and links
# ----------------------------------------------------------------------------
_BUTTON_STYLES = {
    "primary": {"bg": Colors.PRIMARY, "fg": Colors.TEXT_ON_PRIMARY, "hover": Colors.PRIMARY_HOVER},
    "secondary": {"bg": Colors.SURFACE, "fg": Colors.TEXT, "hover": Colors.BG, "border": Colors.BORDER},
    "soft": {"bg": Colors.PRIMARY_LIGHT, "fg": Colors.PRIMARY, "hover": Colors.PRIMARY_LIGHT_HOVER},
    "danger": {"bg": Colors.DANGER, "fg": Colors.TEXT_ON_PRIMARY, "hover": Colors.DANGER_HOVER},
    "danger_soft": {"bg": Colors.DANGER_LIGHT, "fg": Colors.DANGER, "hover": Colors.DANGER_LIGHT_HOVER},
    "disabled": {"bg": Colors.BORDER, "fg": Colors.TEXT_LIGHT, "hover": Colors.BORDER},
}


class FlatButton(tk.Label):
    """A flat, hover-aware button built on a Label (consistent on every OS)."""

    def __init__(self, parent, text, command=None, style="primary", size=10, padx=16, pady=8, **kwargs):
        self._style_name = style
        palette = _BUTTON_STYLES[style]
        super().__init__(
            parent, text=text, bg=palette["bg"], fg=palette["fg"], font=font(size, "bold"),
            padx=padx, pady=pady, cursor="hand2", highlightthickness=1,
            highlightbackground=palette.get("border", palette["bg"]), **kwargs,
        )
        self._command = command
        self._enabled = True
        self.bind("<Enter>", lambda _e: self._apply("hover"))
        self.bind("<Leave>", lambda _e: self._apply("bg"))
        self.bind("<Button-1>", self._on_click)

    def _apply(self, key: str) -> None:
        """Switch between the normal ('bg') and hover ('hover') colour."""
        if self._enabled:
            self.configure(bg=_BUTTON_STYLES[self._style_name][key])

    def _on_click(self, _event) -> None:
        if self._enabled and self._command:
            self._command()

    def set_text(self, text: str) -> None:
        self.configure(text=text)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the button (disabled buttons look greyed out)."""
        self._enabled = enabled
        palette = _BUTTON_STYLES[self._style_name if enabled else "disabled"]
        self.configure(
            bg=palette["bg"], fg=palette["fg"], cursor="hand2" if enabled else "arrow",
            highlightbackground=palette.get("border", palette["bg"]),
        )


class LinkLabel(tk.Label):
    """Clickable text that underlines on hover."""

    def __init__(self, parent, text, command=None, color=Colors.PRIMARY, size=9, bold=True, bg=Colors.SURFACE):
        self._font_plain = font(size, "bold" if bold else "normal")
        self._font_hover = (*self._font_plain[:2], self._font_plain[2] + " underline")
        super().__init__(parent, text=text, fg=color, bg=bg, font=self._font_plain, cursor="hand2")
        self.bind("<Enter>", lambda _e: self.configure(font=self._font_hover))
        self.bind("<Leave>", lambda _e: self.configure(font=self._font_plain))
        if command:
            self.bind("<Button-1>", lambda _e: command())


# ----------------------------------------------------------------------------
# Containers and display widgets
# ----------------------------------------------------------------------------
class Card(tk.Frame):
    """White rounded-look panel with a thin border. Put content in ``card.body``."""

    def __init__(self, parent, padding=(20, 18), bg=Colors.SURFACE, **kwargs):
        super().__init__(
            parent, bg=bg, highlightthickness=1, highlightbackground=Colors.BORDER,
            highlightcolor=Colors.BORDER, **kwargs,
        )
        self.body = tk.Frame(self, bg=bg)
        self.body.pack(fill="both", expand=True, padx=padding[0], pady=padding[1])


class Avatar(tk.Canvas):
    """Circular avatar: shows a (circle-cropped) photo or coloured initials."""

    def __init__(self, parent, name: str, size: int = 40, photo_path: str = "", bg=Colors.SURFACE):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0)
        self._photo = None
        color = avatar_color_for(name, AVATAR_COLORS)
        self.create_oval(1, 1, size - 1, size - 1, fill=color, outline=color)
        self.create_text(size / 2, size / 2, text=initials(name), fill="white",
                         font=font(max(8, size // 3), "bold"))
        if photo_path:
            self._load_photo(photo_path, size)

    def _load_photo(self, path: str, size: int) -> None:
        if Image is None:
            return
        try:
            img = Image.open(path).convert("RGBA")
            side = min(img.size)
            left, top = (img.width - side) // 2, (img.height - side) // 2
            img = img.crop((left, top, left + side, top + side)).resize((size, size))
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
            img.putalpha(mask)
            self._photo = ImageTk.PhotoImage(img)  # keep a reference
            self.create_image(0, 0, image=self._photo, anchor="nw")
        except (OSError, ValueError):
            pass  # keep the initials avatar if the image cannot be read


class Pill(tk.Label):
    """Small coloured tag (skill chips, status badges, category labels)."""

    def __init__(self, parent, text, fg=Colors.PRIMARY, bg=Colors.PRIMARY_LIGHT, size=8, padx=8, pady=2):
        super().__init__(parent, text=text, fg=fg, bg=bg, font=font(size, "bold"), padx=padx, pady=pady)


def status_badge(parent, status: str) -> Pill:
    """Create a coloured badge for a request/account status."""
    fg, bg = STATUS_STYLES.get(status, (Colors.TEXT_MUTED, Colors.BORDER))
    return Pill(parent, status, fg=fg, bg=bg)


class ProgressBar(tk.Canvas):
    """Horizontal progress bar that redraws itself when resized."""

    def __init__(self, parent, value: float, color: str = Colors.PRIMARY, height: int = 8, bg=Colors.SURFACE):
        super().__init__(parent, height=height, bg=bg, highlightthickness=0, bd=0)
        self.value = max(0, min(100, value))
        self.color = color
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None) -> None:
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        self.create_rectangle(0, 0, width, height, fill="#F1F5F9", outline="")
        self.create_rectangle(0, 0, int(width * self.value / 100), height, fill=self.color, outline="")


def stars_text(rating: float, maximum: int = 5) -> str:
    """Return a ★★★★☆ style string for a rating."""
    full = max(0, min(maximum, int(round(rating))))
    return "★" * full + "☆" * (maximum - full)


class StarLabel(tk.Label):
    """Read-only star rating display."""

    def __init__(self, parent, rating: float, size: int = 10, bg=Colors.SURFACE):
        super().__init__(parent, text=stars_text(rating), fg=Colors.STAR, bg=bg, font=font(size))


class StarPicker(tk.Frame):
    """Five clickable stars. ``value`` holds the selected rating (0 = none)."""

    def __init__(self, parent, command=None, size: int = 20, bg=Colors.SURFACE):
        super().__init__(parent, bg=bg)
        self.value = 0
        self._command = command
        self._labels = []
        for index in range(5):
            label = tk.Label(self, text="☆", fg=Colors.STAR, bg=bg, font=font(size), cursor="hand2")
            label.pack(side="left", padx=1)
            label.bind("<Button-1>", lambda _e, n=index + 1: self.set_value(n))
            self._labels.append(label)

    def set_value(self, value: int) -> None:
        self.value = value
        for index, label in enumerate(self._labels):
            label.configure(text="★" if index < value else "☆")
        if self._command:
            self._command(value)


class FeedbackLabel(tk.Label):
    """Inline message line used for validation errors and success notes."""

    def __init__(self, parent, bg=Colors.SURFACE, wraplength=420):
        super().__init__(parent, text="", bg=bg, font=font(9), anchor="w", justify="left", wraplength=wraplength)

    def show_error(self, message: str) -> None:
        self.configure(text=message, fg=Colors.DANGER)

    def show_success(self, message: str) -> None:
        self.configure(text=message, fg=Colors.SUCCESS)

    def clear(self) -> None:
        self.configure(text="")


# ----------------------------------------------------------------------------
# Form inputs
# ----------------------------------------------------------------------------
class PlaceholderEntry(tk.Entry):
    """Entry that shows grey placeholder text until the user types."""

    def __init__(self, parent, placeholder: str = "", show: str = "", **kwargs):
        super().__init__(
            parent, relief="flat", bd=0, highlightthickness=0, font=font(10), fg=Colors.TEXT,
            bg=Colors.SURFACE, insertbackground=Colors.TEXT, readonlybackground=Colors.BG, **kwargs,
        )
        self.placeholder = placeholder
        self._mask_char = show
        self._showing_placeholder = False
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._show_placeholder()

    def _show_placeholder(self) -> None:
        if not self.get() and self.placeholder:
            self._showing_placeholder = True
            self.configure(show="", fg=Colors.TEXT_LIGHT)
            self.insert(0, self.placeholder)

    def _on_focus_in(self, _event) -> None:
        if self._showing_placeholder:
            self.delete(0, "end")
            self._showing_placeholder = False
            self.configure(fg=Colors.TEXT, show=self._mask_char)

    def _on_focus_out(self, _event) -> None:
        if not self.get():
            self._show_placeholder()

    def value(self) -> str:
        """Return the typed text ('' while the placeholder is visible)."""
        return "" if self._showing_placeholder else self.get()

    def set_value(self, text: str) -> None:
        self.delete(0, "end")
        self._showing_placeholder = False
        self.configure(fg=Colors.TEXT, show=self._mask_char)
        self.insert(0, text)
        if not text and not _has_focus(self):
            self._show_placeholder()

    def set_masked(self, masked: bool) -> None:
        """Show or hide characters (used by the 'show password' checkbox)."""
        self._mask_char = "•" if masked else ""
        if not self._showing_placeholder:
            self.configure(show=self._mask_char)


class FormField(tk.Frame):
    """Caption + bordered entry with focus and error highlighting."""

    def __init__(
        self, parent, label: str, placeholder: str = "", show: str = "", bg=Colors.SURFACE,
        input_validator=None, invalid_input_callback=None,
    ):
        super().__init__(parent, bg=bg)
        self._error = False
        self._input_validator = input_validator
        self._invalid_input_callback = invalid_input_callback
        tk.Label(self, text=label.upper(), bg=bg, fg=Colors.TEXT_MUTED, font=font(8, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 4))
        self.box = tk.Frame(self, bg=Colors.SURFACE, highlightthickness=1,
                            highlightbackground=Colors.BORDER, highlightcolor=Colors.BORDER)
        self.box.pack(fill="x")
        self.entry = PlaceholderEntry(self.box, placeholder=placeholder, show="•" if show else "")
        self.entry.pack(fill="x", padx=10, pady=9)
        self.error_label = tk.Label(
            self, bg=bg, fg=Colors.DANGER, font=font(8), anchor="w", justify="left", wraplength=240,
        )
        if input_validator is not None:
            self.entry.configure(
                validate="key",
                validatecommand=(self.entry.register(self._validate_input), "%P"),
            )
        self.entry.bind("<FocusIn>", lambda _e: self._set_border(Colors.PRIMARY), add="+")
        self.entry.bind("<FocusOut>", lambda _e: self._set_border(), add="+")

    def _validate_input(self, value: str) -> bool:
        if self._input_validator(value):
            return True
        if self._invalid_input_callback is not None:
            self._invalid_input_callback()
        return False

    def _set_border(self, color: str = None) -> None:
        if color is None:
            color = Colors.DANGER if self._error else Colors.BORDER
        self.box.configure(highlightbackground=color)

    def value(self) -> str:
        return self.entry.value().strip()

    def raw_value(self) -> str:
        return self.entry.value()

    def set_value(self, text: str) -> None:
        self.entry.set_value(text)

    def clear(self) -> None:
        self.set_error(False)
        self.entry.set_value("")

    def set_error(self, has_error: bool, message: str = "") -> None:
        self._error = has_error
        self._set_border()
        if has_error and message:
            self.error_label.configure(text=message)
            if not self.error_label.winfo_manager():
                self.error_label.pack(fill="x", pady=(3, 0))
        else:
            self.error_label.pack_forget()
            self.error_label.configure(text="")

    def set_readonly(self, readonly: bool = True) -> None:
        self.entry.configure(state="readonly" if readonly else "normal")
        self.box.configure(bg=Colors.BG if readonly else Colors.SURFACE)

    def set_masked(self, masked: bool) -> None:
        self.entry.set_masked(masked)

    def focus(self) -> None:
        self.entry.focus_set()


class ComboField(tk.Frame):
    """Caption + read-only drop-down list (ttk.Combobox)."""

    def __init__(self, parent, label: str, values: list, default: str = None, bg=Colors.SURFACE):
        super().__init__(parent, bg=bg)
        if label:
            tk.Label(self, text=label.upper(), bg=bg, fg=Colors.TEXT_MUTED, font=font(8, "bold"),
                     anchor="w").pack(fill="x", pady=(0, 4))
        self.var = tk.StringVar(value=default if default is not None else (values[0] if values else ""))
        self.combo = ttk.Combobox(self, textvariable=self.var, values=values, state="readonly",
                                  style="App.TCombobox", font=font(10))
        self.combo.pack(fill="x", ipady=4)
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self.combo.selection_clear())

    def value(self) -> str:
        return self.var.get()

    def set_value(self, value: str) -> None:
        self.var.set(value)

    def set_values(self, values: list, default: str = None) -> None:
        self.combo.configure(values=values)
        self.var.set(default if default is not None else (values[0] if values else ""))

    def on_change(self, callback) -> None:
        self.combo.bind("<<ComboboxSelected>>", lambda _e: callback(), add="+")


class TextArea(tk.Frame):
    """Caption + bordered multi-line Text widget with placeholder support."""

    def __init__(self, parent, label: str, placeholder: str = "", height: int = 4, bg=Colors.SURFACE):
        super().__init__(parent, bg=bg)
        self.placeholder = placeholder
        self._showing_placeholder = False
        self._error = False
        if label:
            tk.Label(self, text=label.upper(), bg=bg, fg=Colors.TEXT_MUTED, font=font(8, "bold"),
                     anchor="w").pack(fill="x", pady=(0, 4))
        self.box = tk.Frame(self, bg=Colors.SURFACE, highlightthickness=1,
                            highlightbackground=Colors.BORDER, highlightcolor=Colors.BORDER)
        self.box.pack(fill="x")
        self.text = tk.Text(self.box, height=height, wrap="word", relief="flat", bd=0,
                            highlightthickness=0, font=font(10), fg=Colors.TEXT, bg=Colors.SURFACE,
                            insertbackground=Colors.TEXT, padx=2, pady=2)
        self.text.pack(fill="x", padx=10, pady=8)
        self.error_label = tk.Label(
            self, bg=bg, fg=Colors.DANGER, font=font(8), anchor="w", justify="left", wraplength=520,
        )
        self.text.bind("<FocusIn>", self._on_focus_in)
        self.text.bind("<FocusOut>", self._on_focus_out)
        self._show_placeholder()

    def _set_border(self, color: str = None) -> None:
        if color is None:
            color = Colors.DANGER if self._error else Colors.BORDER
        self.box.configure(highlightbackground=color)

    def _show_placeholder(self) -> None:
        if self.placeholder and not self.text.get("1.0", "end-1c"):
            self._showing_placeholder = True
            self.text.configure(fg=Colors.TEXT_LIGHT)
            self.text.insert("1.0", self.placeholder)

    def _on_focus_in(self, _event) -> None:
        self._set_border(Colors.PRIMARY)
        if self._showing_placeholder:
            self.text.delete("1.0", "end")
            self._showing_placeholder = False
            self.text.configure(fg=Colors.TEXT)

    def _on_focus_out(self, _event) -> None:
        self._set_border()
        if not self.text.get("1.0", "end-1c"):
            self._show_placeholder()

    def value(self) -> str:
        return "" if self._showing_placeholder else self.text.get("1.0", "end-1c").strip()

    def set_value(self, text: str) -> None:
        self.text.delete("1.0", "end")
        self._showing_placeholder = False
        self.text.configure(fg=Colors.TEXT)
        self.text.insert("1.0", text)
        if not text and not _has_focus(self.text):
            self._show_placeholder()

    def clear(self) -> None:
        self.set_error(False)
        self.set_value("")

    def set_error(self, has_error: bool, message: str = "") -> None:
        self._error = has_error
        self._set_border()
        if has_error and message:
            self.error_label.configure(text=message)
            if not self.error_label.winfo_manager():
                self.error_label.pack(fill="x", pady=(3, 0))
        else:
            self.error_label.pack_forget()
            self.error_label.configure(text="")

    def bind_change(self, callback) -> None:
        self.text.bind("<KeyRelease>", lambda _e: callback(), add="+")


# ----------------------------------------------------------------------------
# Scrolling and page layout helpers
# ----------------------------------------------------------------------------
class ScrollableFrame(tk.Frame):
    """A frame whose content (``self.inner``) scrolls vertically when too tall."""

    def __init__(self, parent, bg=Colors.BG):
        super().__init__(parent, bg=bg)
        self._wheel_remainder = 0.0
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, yscrollincrement=20)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_inner_configure(self, _event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self.canvas.itemconfigure(self._window, width=event.width)

    def scroll_units(self, units: int) -> None:
        """Scroll only when the content is taller than the visible area."""
        if self.inner.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(units, "units")

    def scroll_wheel_delta(self, delta: int) -> None:
        """Accumulate small precision-wheel deltas into smooth page scrolling."""
        if self.inner.winfo_height() <= self.canvas.winfo_height():
            return
        self._wheel_remainder -= delta / 60
        units = int(self._wheel_remainder)
        if units:
            self._wheel_remainder -= units
            self.canvas.yview_scroll(units, "units")

    def scroll_to_top(self) -> None:
        self.canvas.yview_moveto(0)


def page_header(parent, title: str, subtitle: str, action_text: str = None, action_command=None) -> tk.Frame:
    """Page title + subtitle (and an optional primary action button on the right)."""
    header = tk.Frame(parent, bg=Colors.BG)
    header.pack(fill="x", pady=(0, 18))
    tk.Frame(header, bg=Colors.PRIMARY, width=4, height=42).pack(side="left", padx=(0, 12), pady=(2, 0))
    texts = tk.Frame(header, bg=Colors.BG)
    texts.pack(side="left")
    tk.Label(texts, text=title, bg=Colors.BG, fg=Colors.TEXT, font=font(20, "bold"), anchor="w").pack(anchor="w")
    tk.Label(texts, text=subtitle, bg=Colors.BG, fg=Colors.TEXT_MUTED, font=font(10), anchor="w").pack(anchor="w", pady=(2, 0))
    if action_text:
        FlatButton(header, action_text, action_command, "primary").pack(side="right", anchor="n")
    return header


def section_title(parent, text: str, bg=Colors.SURFACE, size: int = 13) -> tk.Label:
    """Bold heading used at the top of cards and sections."""
    return tk.Label(parent, text=text, bg=bg, fg=Colors.TEXT, font=font(size, "bold"), anchor="w")


def clear_children(widget: tk.Misc) -> None:
    """Destroy every child of ``widget`` (used before re-rendering lists)."""
    for child in widget.winfo_children():
        child.destroy()


# ----------------------------------------------------------------------------
# Confirmation panels (match the "submitted" / "success" frames in Figma)
# ----------------------------------------------------------------------------
def success_check_panel(parent, message: str, on_back, back_text: str = "Back") -> tk.Frame:
    """Large green tick with a message and a Back button (skill registered, etc.)."""
    card = Card(parent, padding=(30, 30))
    canvas = tk.Canvas(card.body, width=190, height=190, bg=Colors.SURFACE, highlightthickness=0)
    canvas.pack(pady=(10, 14))
    canvas.create_oval(5, 5, 185, 185, fill="#43A047", outline="#43A047")
    canvas.create_line(52, 98, 83, 130, 138, 66, fill="white", width=16, capstyle="round", joinstyle="round")
    tk.Label(card.body, text=message, bg=Colors.SURFACE, fg=Colors.TEXT, font=font(15, "bold")).pack(pady=(0, 16))
    FlatButton(card.body, back_text, on_back, "primary").pack()
    return card


def banner_panel(parent, message: str, color: str, on_back, back_style: str = "danger",
                 back_text: str = "Back") -> tk.Frame:
    """Full-width coloured banner with a message and a Back button."""
    holder = tk.Frame(parent, bg=Colors.BG)
    banner = tk.Frame(holder, bg=color, height=220)
    banner.pack(fill="x")
    banner.pack_propagate(False)
    tk.Label(banner, text=message, bg=color, fg="white", font=font(24, "bold")).pack(expand=True)
    FlatButton(holder, f"◀  {back_text}", on_back, back_style).pack(anchor="w", pady=(16, 0))
    return holder


# ----------------------------------------------------------------------------
# Navigation helpers
# ----------------------------------------------------------------------------
class TabBar(tk.Frame):
    """Underlined text tabs. ``tabs`` is a list of ``(key, label)`` pairs."""

    def __init__(self, parent, tabs: list, active: str, on_select, bg=Colors.BG):
        super().__init__(parent, bg=bg)
        border = tk.Frame(self, height=1, bg=Colors.BORDER)
        border.place(relx=0, rely=1.0, relwidth=1, anchor="sw")
        for key, label in tabs:
            is_active = key == active
            holder = tk.Frame(self, bg=bg)
            holder.pack(side="left", padx=(0, 28))
            title = tk.Label(holder, text=label, bg=bg, cursor="hand2", pady=8,
                             fg=Colors.PRIMARY if is_active else Colors.TEXT_MUTED, font=font(10, "bold"))
            title.pack()
            tk.Frame(holder, height=2, bg=Colors.PRIMARY if is_active else bg).pack(fill="x")
            title.bind("<Button-1>", lambda _e, k=key: on_select(k))


def make_clickable(widget: tk.Misc, command) -> None:
    """Make a widget (and everything inside it) respond to clicks like a button."""
    widget.configure(cursor="hand2")
    widget.bind("<Button-1>", lambda _e: command())
    for child in widget.winfo_children():
        make_clickable(child, command)
