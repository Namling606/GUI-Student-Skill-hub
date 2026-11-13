"""Portfolio showcase (Figma frame: portfolio-screen)."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from config import ICONS, Colors, font
from screens.base import BaseScreen
from utils.helpers import days_ago_text
from utils.validators import validate_portfolio_item
from widgets.components import (
    Card, ComboField, FlatButton, FormField, Pill, TextArea, page_header,
)
from widgets.dialogs import ModalDialog

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover
    Image = ImageTk = None

IMAGE_TYPES = [("Images", "*.png *.jpg *.jpeg *.gif"), ("All files", "*.*")]
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def readable_text_color(hex_color: str) -> str:
    """Dark text on light backgrounds, white text on dark ones."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return Colors.TEXT if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#FFFFFF"


class Thumbnail(tk.Canvas):
    """Work preview: the uploaded image (cover-fit) or a coloured placeholder."""

    def __init__(self, parent, item: dict, height: int = 150):
        super().__init__(parent, height=height, bg=item["color"], highlightthickness=0, bd=0)
        self.item = item
        self._photo = None
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None) -> None:
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        path = self.item.get("image_path", "")
        if path and Image is not None and os.path.exists(path):
            try:
                img = Image.open(path).convert("RGB")
                scale = max(width / img.width, height / img.height)
                img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))))
                left, top = (img.width - width) // 2, (img.height - height) // 2
                self._photo = ImageTk.PhotoImage(img.crop((left, top, left + width, top + height)))
                self.create_image(0, 0, image=self._photo, anchor="nw")
                return
            except (OSError, ValueError):
                pass
        self.create_text(width / 2, height / 2, text=self.item["title"], fill=readable_text_color(self.item["color"]),
                         font=font(13, "bold"), width=max(width - 40, 50), justify="center")


class PortfolioDialog(ModalDialog):
    """Add a new work or edit an existing one. Returns a dict of the fields."""

    def __init__(self, parent, skill_options: list, item: dict = None):
        super().__init__(parent, "Edit work" if item else "Upload new work",
                         heading="Edit work" if item else "Upload new work")
        self.image_path = item["image_path"] if item else ""
        self.title_field = FormField(self.body, "Title", "e.g. Campus Event Poster")
        self.title_field.pack(fill="x", ipadx=150, pady=(0, 10))
        self.tag_field = ComboField(self.body, "Skill tag", skill_options,
                                    default=item["skill_tag"] if item and item["skill_tag"] in skill_options else None)
        self.tag_field.pack(fill="x", pady=(0, 10))
        self.description_field = TextArea(self.body, "Description (optional)", height=3)
        self.description_field.pack(fill="x", pady=(0, 10))

        image_row = tk.Frame(self.body, bg=Colors.SURFACE)
        image_row.pack(fill="x")
        FlatButton(image_row, "Choose image…", self._choose_image, "secondary", size=9).pack(side="left")
        self.image_label = tk.Label(image_row, text="", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(9))
        self.image_label.pack(side="left", padx=10)

        if item:
            self.title_field.set_value(item["title"])
            self.description_field.set_value(item["description"])
        self._refresh_image_label()
        self.add_buttons("Save" if item else "Upload", self._submit)
        self.after(100, self.title_field.focus)

    def _refresh_image_label(self) -> None:
        self.image_label.configure(text=os.path.basename(self.image_path) if self.image_path else "No image selected")

    def _choose_image(self) -> None:
        path = filedialog.askopenfilename(parent=self, title="Choose an image", filetypes=IMAGE_TYPES)
        if not path:
            return
        if not path.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            self.status.show_error("Please choose a PNG, JPG or GIF image.")
        elif os.path.getsize(path) > MAX_IMAGE_BYTES:
            self.status.show_error("The image must be smaller than 8 MB.")
        else:
            self.image_path = path
            self.status.clear()
            self._refresh_image_label()

    def _submit(self) -> None:
        title, tag = self.title_field.value(), self.tag_field.value()
        ok, message = validate_portfolio_item(title, tag)
        self.title_field.set_error(not ok)
        if not ok:
            self.status.show_error(message)
            return
        if len(self.description_field.value()) > 200:
            self.description_field.set_error(True)
            self.status.show_error("Description must be 200 characters or fewer.")
            return
        self.finish({"title": title, "tag": tag, "description": self.description_field.value(),
                     "image_path": self.image_path})


class WorkViewer(ModalDialog):
    """Read-only popup showing one portfolio work in more detail."""

    def __init__(self, parent, item: dict):
        super().__init__(parent, item["title"])
        thumb = Thumbnail(self.body, item, height=220)
        thumb.pack(fill="x", ipadx=230)
        tk.Label(self.body, text=item["title"], bg=Colors.SURFACE, fg=Colors.TEXT, font=font(14, "bold"),
                 anchor="w").pack(fill="x", pady=(14, 4))
        meta = tk.Frame(self.body, bg=Colors.SURFACE)
        meta.pack(fill="x")
        Pill(meta, item["skill_tag"]).pack(side="left")
        tk.Label(meta, text=f"Added {days_ago_text(item['days_ago'])}", bg=Colors.SURFACE, fg=Colors.TEXT_LIGHT,
                 font=font(9)).pack(side="left", padx=8)
        tk.Label(self.body, text=item["description"] or "No description provided.", bg=Colors.SURFACE,
                 fg=Colors.TEXT_MUTED, font=font(10), wraplength=440, justify="left", anchor="w").pack(fill="x", pady=(12, 0))
        FlatButton(self.buttons, "Close", self.cancel, "primary").pack(side="right")


class PortfolioScreen(BaseScreen):
    """Grid of the student's showcased works with view / edit / delete actions."""

    def render(self, upload: bool = False, **_ignored) -> None:
        page_header(self.content, "My Portfolio", "Showcase your creative deliverables and technical achievements to get requested.",
                    f"{ICONS['upload']}  Upload New Work", self._upload)
        items = self.store.get_portfolio(self.user["student_id"])
        if not items:
            card = Card(self.content, padding=(24, 36))
            card.pack(fill="x")
            tk.Label(card.body, text="Your portfolio is empty. Upload your first work to get discovered!",
                     bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(10)).pack()
        else:
            grid = tk.Frame(self.content, bg=Colors.BG)
            grid.pack(fill="x")
            grid.columnconfigure((0, 1, 2), weight=1, uniform="portfolio")
            for index, item in enumerate(items):
                self._build_card(grid, item).grid(
                    row=index // 3, column=index % 3, sticky="nsew", pady=(0, 16),
                    padx=(0 if index % 3 == 0 else 8, 0 if index % 3 == 2 else 8))
        if upload:
            self.after(200, self._upload)  # opened from a dashboard quick action

    def _build_card(self, parent, item: dict) -> Card:
        card = Card(parent, padding=(0, 0))
        Thumbnail(card.body, item).pack(fill="x")
        info = tk.Frame(card.body, bg=Colors.SURFACE)
        info.pack(fill="x", padx=16, pady=14)
        tk.Label(info, text=item["title"], bg=Colors.SURFACE, fg=Colors.TEXT, font=font(11, "bold"), anchor="w").pack(fill="x")
        meta = tk.Frame(info, bg=Colors.SURFACE)
        meta.pack(fill="x", pady=(4, 10))
        Pill(meta, item["skill_tag"]).pack(side="left")
        tk.Label(meta, text=f"Added {days_ago_text(item['days_ago'])}", bg=Colors.SURFACE, fg=Colors.TEXT_LIGHT,
                 font=font(8)).pack(side="left", padx=8)
        tk.Frame(info, height=1, bg=Colors.BORDER).pack(fill="x", pady=(0, 10))
        buttons = tk.Frame(info, bg=Colors.SURFACE)
        buttons.pack(fill="x")
        FlatButton(buttons, "View Work", lambda: WorkViewer(self, item).show(), "secondary", size=9).pack(side="left")
        FlatButton(buttons, ICONS["delete"], lambda: self._delete(item), "danger_soft", size=9, padx=12).pack(side="right")
        FlatButton(buttons, "Edit", lambda: self._edit(item), "secondary", size=9).pack(side="right", padx=6)
        return card

    def _skill_options(self) -> list:
        names = [s["name"] for s in self.store.get_skills(self.user["student_id"])]
        return names + ["Other"]

    def _upload(self) -> None:
        data = PortfolioDialog(self, self._skill_options()).show()
        if data:
            self.store.add_portfolio_item(self.user["student_id"], data["title"], data["tag"],
                                          data["description"], data["image_path"])
            self.show()

    def _edit(self, item: dict) -> None:
        options = self._skill_options()
        if item["skill_tag"] not in options:
            options.insert(0, item["skill_tag"])
        data = PortfolioDialog(self, options, item).show()
        if data:
            self.store.update_portfolio_item(item["item_id"], title=data["title"], skill_tag=data["tag"],
                                             description=data["description"], image_path=data["image_path"])
            self.show()

    def _delete(self, item: dict) -> None:
        if messagebox.askyesno("Delete work", f"Delete '{item['title']}' from your portfolio?"):
            self.store.delete_portfolio_item(item["item_id"])
            self.show()
