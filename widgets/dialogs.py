"""Modal dialog windows (text prompt, choice prompt) built on one base class."""

import tkinter as tk

from config import Colors, font
from widgets.components import ComboField, FeedbackLabel, FlatButton, FormField


class ModalDialog(tk.Toplevel):
    """Base class: a centred, modal window with a body, status line and buttons."""

    def __init__(self, parent, title: str, heading: str = ""):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=Colors.SURFACE)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.result = None
        if heading:
            tk.Label(self, text=heading, bg=Colors.SURFACE, fg=Colors.TEXT,
                     font=font(14, "bold")).pack(anchor="w", padx=24, pady=(20, 0))
        self.body = tk.Frame(self, bg=Colors.SURFACE)
        self.body.pack(fill="both", expand=True, padx=24, pady=(14, 6))
        self.status = FeedbackLabel(self, wraplength=380)
        self.status.pack(fill="x", padx=24)
        self.buttons = tk.Frame(self, bg=Colors.SURFACE)
        self.buttons.pack(fill="x", padx=24, pady=(8, 20))
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Escape>", lambda _e: self.cancel())

    def add_buttons(self, ok_text: str, on_ok) -> None:
        FlatButton(self.buttons, ok_text, on_ok, "primary").pack(side="right")
        FlatButton(self.buttons, "Cancel", self.cancel, "secondary").pack(side="right", padx=(0, 8))

    def cancel(self) -> None:
        self.result = None
        self.destroy()

    def finish(self, result) -> None:
        self.result = result
        self.destroy()

    def show(self):
        """Centre the dialog over its parent, block until closed, return the result."""
        self.update_idletasks()
        root = self.master.winfo_toplevel()
        x = root.winfo_rootx() + (root.winfo_width() - self.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        self.wait_window(self)
        return self.result


class TextPromptDialog(ModalDialog):
    """Ask for one line of text. ``validator(text) -> (ok, message)``."""

    def __init__(self, parent, title: str, label: str, validator, placeholder: str = "", ok_text: str = "Save"):
        super().__init__(parent, title, heading=title)
        self._validator = validator
        self.field = FormField(self.body, label, placeholder)
        self.field.pack(fill="x", ipadx=140)
        self.add_buttons(ok_text, self._submit)
        self.bind("<Return>", lambda _e: self._submit())
        self.after(100, self.field.focus)

    def _submit(self) -> None:
        text = self.field.value()
        ok, message = self._validator(text)
        if not ok:
            self.field.set_error(True)
            self.status.show_error(message)
            return
        self.finish(text)


class ChoiceDialog(ModalDialog):
    """Ask the user to choose one option from a drop-down list."""

    def __init__(self, parent, title: str, label: str, options: list, ok_text: str = "Submit"):
        super().__init__(parent, title, heading=title)
        self.combo = ComboField(self.body, label, options)
        self.combo.pack(fill="x", ipadx=140)
        self.add_buttons(ok_text, lambda: self.finish(self.combo.value()))


def ask_text(parent, title, label, validator, placeholder="", ok_text="Save"):
    """Show a TextPromptDialog and return the entered text (or None)."""
    return TextPromptDialog(parent, title, label, validator, placeholder, ok_text).show()


def ask_choice(parent, title, label, options, ok_text="Submit"):
    """Show a ChoiceDialog and return the chosen option (or None)."""
    return ChoiceDialog(parent, title, label, options, ok_text).show()
