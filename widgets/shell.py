"""The persistent application frame: sidebar navigation and top bar."""

import tkinter as tk

from config import ICONS, INSTITUTION_BADGE, SIDEBAR_WIDTH, TOPBAR_HEIGHT, APP_TITLE, Colors, font
from widgets.components import Avatar, Pill


class NavItem(tk.Frame):
    """One clickable row in the sidebar (icon + label) with hover/active states."""

    def __init__(self, parent, icon: str, text: str, command, danger: bool = False):
        super().__init__(parent, bg=Colors.SURFACE, cursor="hand2")
        self._danger = danger
        self._active = False
        self._command = command
        self.indicator = tk.Frame(self, bg=Colors.SURFACE, width=3)
        self.indicator.pack(side="left", fill="y")
        self.icon = tk.Label(self, text=icon, font=font(12), bg=Colors.SURFACE, width=2, cursor="hand2")
        self.icon.pack(side="left", padx=(12, 6), pady=9)
        self.label = tk.Label(self, text=text, font=font(10, "bold" if danger else "normal"),
                              bg=Colors.SURFACE, anchor="w", cursor="hand2")
        self.label.pack(side="left", fill="x", expand=True)
        for widget in (self, self.icon, self.label):
            widget.bind("<Button-1>", lambda _e: self._command())
            widget.bind("<Enter>", lambda _e: self._paint(hover=True))
            widget.bind("<Leave>", lambda _e: self._paint())
        self._paint()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._paint()

    def _paint(self, hover: bool = False) -> None:
        if self._active:
            bg = Colors.DANGER_LIGHT if self._danger else Colors.PRIMARY_LIGHT
            fg = Colors.DANGER if self._danger else Colors.PRIMARY
        else:
            bg = Colors.BG if hover else Colors.SURFACE
            fg = Colors.DANGER if self._danger else Colors.TEXT_MUTED
        for widget in (self, self.icon, self.label):
            widget.configure(bg=bg)
        self.indicator.configure(bg=fg if self._active else bg)
        self.icon.configure(fg=fg)
        self.label.configure(fg=fg)


class Sidebar(tk.Frame):
    """Left navigation panel: brand, navigation items and logout."""

    def __init__(self, parent, items: list, on_navigate, on_logout, admin_mode: bool = False):
        super().__init__(parent, bg=Colors.SURFACE, width=SIDEBAR_WIDTH)
        self.pack_propagate(False)
        tk.Frame(self, width=1, bg=Colors.BORDER).pack(side="right", fill="y")
        self._items = {}

        brand = tk.Frame(self, bg=Colors.SURFACE)
        brand.pack(fill="x", padx=18, pady=(20, 22))
        logo = tk.Canvas(brand, width=36, height=36, bg=Colors.SURFACE, highlightthickness=0)
        logo.pack(side="left")
        logo.create_oval(0, 0, 36, 36, fill=Colors.PRIMARY, outline=Colors.PRIMARY)
        logo.create_text(18, 18, text=ICONS["logo"], font=font(14), fill="white")
        names = tk.Frame(brand, bg=Colors.SURFACE)
        names.pack(side="left", padx=(10, 0))
        tk.Label(names, text="StudentSkill", bg=Colors.SURFACE, fg=Colors.TEXT, font=font(11, "bold")).pack(anchor="w")
        tk.Label(names, text="Admin Hub" if admin_mode else "Campus Hub", bg=Colors.SURFACE,
                 fg=Colors.DANGER if admin_mode else Colors.PRIMARY, font=font(8, "bold")).pack(anchor="w")

        nav = tk.Frame(self, bg=Colors.SURFACE)
        nav.pack(fill="x", padx=12)
        for key, label, icon_key, danger in items:
            item = NavItem(nav, ICONS[icon_key], label, lambda k=key: on_navigate(k), danger=danger)
            item.pack(fill="x", pady=2)
            self._items[key] = item

        footer = tk.Frame(self, bg=Colors.SURFACE)
        footer.pack(side="bottom", fill="x", padx=12, pady=16)
        tk.Frame(footer, height=1, bg=Colors.BORDER).pack(fill="x", pady=(0, 12))
        NavItem(footer, ICONS["logout"], "Logout", on_logout, danger=True).pack(fill="x")

    def set_active(self, key: str) -> None:
        for item_key, item in self._items.items():
            item.set_active(item_key == key)


class Topbar(tk.Frame):
    """Top header: app name + badge on the left, signed-in user on the right."""

    def __init__(self, parent, user: dict, admin_mode: bool = False):
        super().__init__(parent, bg=Colors.SURFACE, height=TOPBAR_HEIGHT)
        self.pack_propagate(False)
        self._admin_mode = admin_mode
        tk.Frame(self, height=1, bg=Colors.BORDER).pack(side="bottom", fill="x")

        left = tk.Frame(self, bg=Colors.SURFACE)
        left.pack(side="left", padx=28)
        tk.Label(left, text=APP_TITLE, bg=Colors.SURFACE, fg=Colors.TEXT, font=font(13, "bold")).pack(side="left")
        if admin_mode:
            Pill(left, "Hub Administrator Mode", fg=Colors.DANGER, bg=Colors.DANGER_LIGHT).pack(side="left", padx=10)
        else:
            Pill(left, INSTITUTION_BADGE).pack(side="left", padx=10)

        self.right = tk.Frame(self, bg=Colors.SURFACE)
        self.right.pack(side="right", padx=28)
        self.update_user(user)

    def update_user(self, user: dict) -> None:
        """Redraw the user area (called after the profile is edited)."""
        for child in self.right.winfo_children():
            child.destroy()
        texts = tk.Frame(self.right, bg=Colors.SURFACE)
        texts.pack(side="left", padx=(0, 10))
        tk.Label(texts, text=user["full_name"], bg=Colors.SURFACE, fg=Colors.TEXT,
                 font=font(10, "bold"), anchor="e").pack(anchor="e")
        tk.Label(texts, text=user["year_label"], bg=Colors.SURFACE, fg=Colors.TEXT_MUTED,
                 font=font(8), anchor="e").pack(anchor="e")
        Avatar(self.right, user["full_name"], size=38, photo_path=user.get("photo_path", ""),
               bg=Colors.SURFACE).pack(side="left")
