"""Profile builder (Figma frames: profile-screen, profile-screen confirmation)."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from config import ICONS, Colors, font
from screens.base import BaseScreen
from utils.helpers import truncate
from utils.validators import (
    is_name_input, validate_achievement, validate_campus_email, validate_course, validate_full_name,
    validate_profile,
)
from widgets.components import (
    Avatar, Card, FeedbackLabel, FlatButton, FormField, Pill, TextArea, page_header,
    section_title, success_check_panel,
)
from widgets.dialogs import ask_text

MAX_PHOTO_BYTES = 5 * 1024 * 1024
PHOTO_TYPES = [("Images", "*.png *.jpg *.jpeg *.gif"), ("All files", "*.*")]


class ProfileScreen(BaseScreen):
    """Edit personal information with a live 'public directory' preview."""

    def render(self, **params) -> None:
        if params.get("saved"):
            page_header(self.content, "Your Profile Builder", "Your changes have been saved.")
            panel = success_check_panel(self.content, "Profile updated successfully!", lambda: self.show())
            panel.pack(fill="x")
            return

        # Working copies - only written to the store when 'Save' is pressed.
        self.photo_path = self.user.get("photo_path", "")
        self.achievements = [a["text"] for a in self.store.get_achievements(self.user["student_id"])]

        page_header(self.content, "Your Profile Builder",
                    "Customize how campus employers and fellow students find and view your talent profile.")
        columns = tk.Frame(self.content, bg=Colors.BG)
        columns.pack(fill="x")
        columns.columnconfigure(0, weight=3, uniform="profile")
        columns.columnconfigure(1, weight=2, uniform="profile")
        self._build_preview(columns).grid(row=0, column=1, sticky="new", padx=(12, 0))
        self._build_form(columns).grid(row=0, column=0, sticky="new", padx=(0, 12))
        self._update_preview()

    # ------------------------------------------------------------------
    # Edit form
    # ------------------------------------------------------------------
    def _build_form(self, parent) -> Card:
        card = Card(parent, padding=(26, 24))
        body = card.body
        section_title(body, "Edit Information", size=14).pack(anchor="w", pady=(0, 14))

        self.photo_row = tk.Frame(body, bg=Colors.SURFACE)
        self.photo_row.pack(fill="x", pady=(0, 16))
        self._render_photo_row()

        grid = tk.Frame(body, bg=Colors.SURFACE)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="pf")
        user = self.user
        self.fields = {
            "full_name": FormField(
                grid, "Full name", input_validator=is_name_input,
                invalid_input_callback=lambda: self._show_profile_field_error(
                    "full_name", "Use letters, spaces, apostrophes, periods, or hyphens in a name."
                ),
            ),
            "student_id": FormField(grid, "Student ID"),
            "course": FormField(grid, "Course & degree"),
            "email": FormField(grid, "Campus email"),
        }
        values = {"full_name": user["full_name"], "student_id": user["student_id"],
                  "course": user["course"], "email": user["email"]}
        for index, key in enumerate(["full_name", "student_id", "course", "email"]):
            field = self.fields[key]
            field.set_value(values[key])
            field.grid(row=index // 2, column=index % 2, sticky="ew", pady=(0, 12),
                       padx=(0, 8) if index % 2 == 0 else (8, 0))
        self.fields["student_id"].set_readonly(True)  # the ID is the primary key

        self.bio = TextArea(body, "Biography", height=4)
        self.bio.set_value(user["bio"])
        self.bio.pack(fill="x", pady=(0, 14))

        tk.Label(body, text="ACHIEVEMENTS", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(8, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 6))
        self.achievement_list = tk.Frame(body, bg=Colors.SURFACE)
        self.achievement_list.pack(fill="x")
        self._render_achievements()
        FlatButton(body, f"{ICONS['plus']}  Add Achievement", self._add_achievement, "secondary").pack(
            anchor="w", pady=(8, 0))

        tk.Frame(body, height=1, bg=Colors.BORDER).pack(fill="x", pady=18)
        self.status = FeedbackLabel(body, wraplength=520)
        self.status.pack(fill="x", pady=(0, 6))
        self._profile_error_field = None
        self._profile_last_values = {key: self.fields[key].raw_value() for key in ("full_name", "course", "email")}
        for key in self._profile_last_values:
            self.fields[key].entry.bind("<FocusOut>", lambda _e, field_key=key: self._validate_profile_field(field_key),
                                        add="+")
            self.fields[key].entry.bind("<KeyRelease>", lambda _e, field_key=key: self._profile_field_changed(field_key),
                                        add="+")
        self._profile_initial_values = self._current_profile_values()
        self._update_profile_actions()

        for key in ("full_name", "course"):
            self.fields[key].entry.bind("<KeyRelease>", lambda _e: self._update_preview(), add="+")
        for key in self._profile_last_values:
            self.fields[key].entry.bind("<<Paste>>", lambda _e, field_key=key: self._profile_field_changed(field_key),
                                        add="+")
            self.fields[key].entry.bind("<<Cut>>", lambda _e, field_key=key: self._profile_field_changed(field_key),
                                        add="+")
        self.bio.bind_change(self._update_preview)
        self.bio.bind_change(self._update_profile_actions)
        self.bio.text.bind("<<Paste>>", lambda _e: self._update_profile_actions(), add="+")
        self.bio.text.bind("<<Cut>>", lambda _e: self._update_profile_actions(), add="+")
        return card

    def _current_profile_values(self) -> tuple:
        return (
            tuple(self.fields[key].raw_value() for key in ("full_name", "course", "email")),
            self.bio.value(),
            self.photo_path,
            tuple(self.achievements),
        )

    def _update_profile_actions(self) -> None:
        if self._current_profile_values() == self._profile_initial_values:
            self.save_button.pack_forget()
            self.discard_button.pack_forget()
            return
        if not self.discard_button.winfo_manager():
            self.discard_button.pack(side="right")
        if not self.save_button.winfo_manager():
            self.save_button.pack(side="right", padx=(0, 10))

    def _show_profile_field_error(self, key: str, message: str) -> None:
        self._profile_error_field = key
        self.fields[key].set_error(True, message)
        self.status.clear()

    def _validate_profile_field(self, key: str) -> None:
        validators = {
            "full_name": validate_full_name,
            "course": validate_course,
            "email": validate_campus_email,
        }
        ok, message = validators[key](self.fields[key].value())
        self.fields[key].set_error(not ok, message if not ok else "")
        if not ok:
            self._show_profile_field_error(key, message)
        elif self._profile_error_field == key:
            self._profile_error_field = None

    def _profile_field_changed(self, key: str) -> None:
        value = self.fields[key].raw_value()
        changed = value != self._profile_last_values[key]
        self._profile_last_values[key] = value
        if changed and self._profile_error_field == key:
            self._validate_profile_field(key)
        self._update_profile_actions()

    def _render_photo_row(self) -> None:
        for child in self.photo_row.winfo_children():
            child.destroy()
        Avatar(self.photo_row, self.user["full_name"], size=64, photo_path=self.photo_path).pack(side="left")
        side = tk.Frame(self.photo_row, bg=Colors.SURFACE)
        side.pack(side="left", padx=14)
        tk.Label(side, text="Profile Photograph", bg=Colors.SURFACE, fg=Colors.TEXT,
                 font=font(10, "bold")).pack(anchor="w", pady=(0, 6))
        buttons = tk.Frame(side, bg=Colors.SURFACE)
        buttons.pack(anchor="w")
        FlatButton(buttons, "Change Photo", self._change_photo, "secondary", size=9).pack(side="left")
        FlatButton(buttons, "Remove", self._remove_photo, "danger_soft", size=9).pack(side="left", padx=8)

    def _render_achievements(self) -> None:
        for child in self.achievement_list.winfo_children():
            child.destroy()
        if not self.achievements:
            tk.Label(self.achievement_list, text="No achievements added yet.", bg=Colors.SURFACE,
                     fg=Colors.TEXT_LIGHT, font=font(9)).pack(anchor="w", pady=4)
        for index, text in enumerate(self.achievements):
            row = tk.Frame(self.achievement_list, bg=Colors.SURFACE, highlightthickness=1,
                           highlightbackground=Colors.BORDER)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=text, bg=Colors.SURFACE, fg=Colors.TEXT, font=font(9), anchor="w",
                     wraplength=420, justify="left").pack(side="left", padx=10, pady=8)
            delete = tk.Label(row, text=ICONS["delete"], bg=Colors.SURFACE, fg=Colors.DANGER,
                              font=font(10, "bold"), cursor="hand2")
            delete.pack(side="right", padx=12)
            delete.bind("<Button-1>", lambda _e, i=index: self._remove_achievement(i))

    # ------------------------------------------------------------------
    # Live preview card
    # ------------------------------------------------------------------
    def _build_preview(self, parent) -> tk.Frame:
        holder = tk.Frame(parent, bg=Colors.BG)
        tk.Label(holder, text="PUBLIC DIRECTORY PREVIEW", bg=Colors.BG, fg=Colors.TEXT_MUTED,
                 font=font(9, "bold"), anchor="w").pack(fill="x", pady=(0, 8))
        self.preview_card = Card(holder, padding=(20, 18))
        self.preview_card.pack(fill="x")
        self.profile_actions = tk.Frame(holder, bg=Colors.BG)
        self.profile_actions.pack(fill="x", pady=(12, 0))
        self.save_button = FlatButton(self.profile_actions, "Save Changes", self._save, "primary")
        self.discard_button = FlatButton(self.profile_actions, "Discard Changes", lambda: self.show(), "secondary")
        return holder

    def _update_preview(self) -> None:
        body = self.preview_card.body
        for child in body.winfo_children():
            child.destroy()
        user = self.user
        name = self.fields["full_name"].value() or user["full_name"]
        course = self.fields["course"].value() or user["course"]
        bio = self.bio.value()

        top = tk.Frame(body, bg=Colors.SURFACE)
        top.pack(fill="x")
        Avatar(top, name, size=56, photo_path=self.photo_path).pack(side="left")
        texts = tk.Frame(top, bg=Colors.SURFACE)
        texts.pack(side="left", padx=12)
        tk.Label(texts, text=name, bg=Colors.SURFACE, fg=Colors.TEXT, font=font(13, "bold")).pack(anchor="w")
        tk.Label(texts, text=f"{course} • {user['year_label']}", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED,
                 font=font(9)).pack(anchor="w")
        rating = tk.Frame(texts, bg=Colors.SURFACE)
        rating.pack(anchor="w")
        tk.Label(rating, text="★", bg=Colors.SURFACE, fg=Colors.STAR, font=font(9)).pack(side="left")
        tk.Label(rating, text=f" {user['rating']:.1f} ({int(user['review_count'])} reviews)", bg=Colors.SURFACE,
                 fg=Colors.TEXT, font=font(9, "bold")).pack(side="left")

        tk.Label(body, text="TOP CAPABILITIES", bg=Colors.SURFACE, fg=Colors.TEXT_LIGHT, font=font(8, "bold"),
                 anchor="w").pack(fill="x", pady=(16, 6))
        chips = tk.Frame(body, bg=Colors.SURFACE)
        chips.pack(fill="x")
        for skill in self.store.top_skills(user["student_id"], 4):
            Pill(chips, skill).pack(side="left", padx=(0, 6))

        tk.Label(body, text="ABOUT ME", bg=Colors.SURFACE, fg=Colors.TEXT_LIGHT, font=font(8, "bold"),
                 anchor="w").pack(fill="x", pady=(16, 6))
        tk.Label(body, text=truncate(bio, 170) if bio else "Add a short biography to introduce yourself.",
                 bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(9), wraplength=330, justify="left",
                 anchor="w").pack(fill="x")

        FlatButton(body, f"{ICONS['requests']}  Request Skill Help", self._preview_request, "primary").pack(
            fill="x", pady=(16, 8))
        FlatButton(body, "View Full Student Portfolio", lambda: self.navigate("portfolio"), "secondary").pack(fill="x")

    @staticmethod
    def _preview_request() -> None:
        messagebox.showinfo("Preview", "Other students see this button on your profile to request your help.")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _change_photo(self) -> None:
        path = filedialog.askopenfilename(title="Choose a profile photo", filetypes=PHOTO_TYPES)
        if not path:
            return
        error = self._check_photo(path)
        if error:
            self.status.show_error(error)
            return
        self.photo_path = path
        self.status.clear()
        self._render_photo_row()
        self._update_preview()
        self._update_profile_actions()

    @staticmethod
    def _check_photo(path: str) -> str:
        """Return an error message if the file is not a usable photo, else ''."""
        if not path.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            return "Please choose a PNG, JPG or GIF image."
        try:
            if os.path.getsize(path) > MAX_PHOTO_BYTES:
                return "The photo must be smaller than 5 MB."
        except OSError:
            return "That file could not be read."
        try:
            from PIL import Image
            with Image.open(path) as img:
                img.verify()
        except Exception:  # corrupt or unsupported image
            return "That file is not a valid image."
        return ""

    def _remove_photo(self) -> None:
        self.photo_path = ""
        self._render_photo_row()
        self._update_preview()
        self._update_profile_actions()

    def _add_achievement(self) -> None:
        if len(self.achievements) >= 6:
            self.status.show_error("You can list up to 6 achievements.")
            return
        text = ask_text(self, "Add achievement", "Achievement", validate_achievement,
                        placeholder="e.g. Winner - Inter-college Quiz 2025", ok_text="Add")
        if text:
            self.achievements.append(text)
            self.status.clear()
            self._render_achievements()
            self._update_profile_actions()

    def _remove_achievement(self, index: int) -> None:
        del self.achievements[index]
        self._render_achievements()
        self._update_profile_actions()

    def _save(self) -> None:
        name, email = self.fields["full_name"].value(), self.fields["email"].value()
        course, bio = self.fields["course"].value(), self.bio.value()
        errors = validate_profile(name, email, course, bio)
        for key in ("full_name", "email", "course"):
            self.fields[key].set_error(key in errors, errors.get(key, ""))
        self.bio.set_error("bio" in errors, errors.get("bio", ""))
        if errors:
            self.status.clear()
            return
        try:
            self.store.update_profile(
                self.user["student_id"], full_name=name, email=email, course=course,
                bio=bio, photo_path=self.photo_path,
            )
        except ValueError as exc:
            self.fields["email"].set_error(True, str(exc))
            return
        self.store.replace_achievements(self.user["student_id"], self.achievements)
        self.app.refresh_user()
        self.show(saved=True)
