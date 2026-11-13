"""Base class shared by every content page shown inside the application shell."""

import tkinter as tk

from config import Colors
from widgets.components import ScrollableFrame, clear_children


class BaseScreen(tk.Frame):
    """A scrollable page. Subclasses implement ``render(**params)``.

    ``show()`` is called by the app every time the page is opened; it clears
    the previous content and re-renders it, so data is always fresh.
    """

    def __init__(self, parent, app):
        super().__init__(parent, bg=Colors.BG)
        self.app = app
        self.store = app.store
        self.params = {}
        self.scroll = ScrollableFrame(self, bg=Colors.BG)
        self.scroll.pack(fill="both", expand=True)
        self.content = None

    @property
    def user(self) -> dict:
        """The signed-in user's record."""
        return self.app.user

    def show(self, **params) -> None:
        """(Re)build the page. ``params`` select a sub-view or carry a message."""
        self.params = params
        self.scroll.scroll_to_top()
        clear_children(self.scroll.inner)
        self.content = tk.Frame(self.scroll.inner, bg=Colors.BG)
        self.content.pack(fill="both", expand=True, padx=32, pady=26)
        self.render(**params)

    def render(self, **params) -> None:
        raise NotImplementedError

    def navigate(self, key: str, **params) -> None:
        self.app.navigate(key, **params)
