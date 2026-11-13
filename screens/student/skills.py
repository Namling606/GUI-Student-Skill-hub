"""Skill inventory (Figma frames: skills-screen, skills-screen confirmation)."""

import tkinter as tk
from tkinter import messagebox

from config import ICONS, SKILL_CATEGORIES, SKILL_LEVELS, Colors, font
from screens.base import BaseScreen
from utils.validators import validate_skill
from widgets.components import (
    Card, ComboField, FeedbackLabel, FlatButton, FormField, Pill, ProgressBar, TextArea, page_header,
    section_title, success_check_panel,
)


def proficiency_color(percent: int) -> str:
    """Bar colour used in the design: blue (high), orange (medium), green (low)."""
    if percent >= 80:
        return Colors.PRIMARY
    if percent >= 50:
        return Colors.WARNING
    return Colors.SUCCESS


class SkillsScreen(BaseScreen):
    """List of the student's skills plus a form to register a new one."""

    def render(self, **params) -> None:
        page_header(self.content, "Your Skill Inventory",
                    "Manage the skills you list for peers to discover and request. Keep your levels updated.")
        if params.get("confirmed"):
            panel = success_check_panel(self.content, params["confirmed"], lambda: self.show())
            panel.pack(anchor="w", fill="x")
            return

        columns = tk.Frame(self.content, bg=Colors.BG)
        columns.pack(fill="x")
        columns.columnconfigure(0, weight=3, uniform="skills")
        columns.columnconfigure(1, weight=2, uniform="skills")
        self._build_list(columns).grid(row=0, column=0, sticky="new", padx=(0, 12))
        self._build_form(columns).grid(row=0, column=1, sticky="new", padx=(12, 0))

    # ------------------------------------------------------------------
    def _build_list(self, parent) -> tk.Frame:
        skills = self.store.get_skills(self.user["student_id"])
        holder = tk.Frame(parent, bg=Colors.BG)
        tk.Label(holder, text=f"My Registered Skills ({len(skills)})", bg=Colors.BG, fg=Colors.TEXT,
                 font=font(12, "bold"), anchor="w").pack(fill="x", pady=(0, 10))
        if not skills:
            tk.Label(holder, text="You have not registered any skills yet. Use the form to add your first one.",
                     bg=Colors.BG, fg=Colors.TEXT_MUTED, font=font(10), wraplength=480, justify="left").pack(anchor="w")
        for skill in skills:
            self._build_skill_card(holder, skill).pack(fill="x", pady=(0, 12))
        return holder

    def _build_skill_card(self, parent, skill: dict) -> Card:
        card = Card(parent, padding=(18, 14))
        top = tk.Frame(card.body, bg=Colors.SURFACE)
        top.pack(fill="x")
        texts = tk.Frame(top, bg=Colors.SURFACE)
        texts.pack(side="left")
        tk.Label(texts, text=skill["name"], bg=Colors.SURFACE, fg=Colors.TEXT, font=font(12, "bold")).pack(anchor="w")
        tk.Label(texts, text=skill["category"], bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(9)).pack(anchor="w")
        FlatButton(top, ICONS["delete"], lambda s=skill: self._delete(s), "danger_soft", padx=14, pady=6).pack(side="right")
        Pill(top, skill["level"]).pack(side="right", padx=12)

        meta = tk.Frame(card.body, bg=Colors.SURFACE)
        meta.pack(fill="x", pady=(10, 4))
        tk.Label(meta, text="Proficiency Estimate", bg=Colors.SURFACE, fg=Colors.TEXT, font=font(8, "bold")).pack(side="left")
        tk.Label(meta, text=f"{int(skill['proficiency'])}%", bg=Colors.SURFACE, fg=Colors.TEXT, font=font(8, "bold")).pack(side="right")
        ProgressBar(card.body, skill["proficiency"], proficiency_color(skill["proficiency"])).pack(fill="x")
        return card

    def _build_form(self, parent) -> Card:
        card = Card(parent, padding=(24, 22))
        body = card.body
        section_title(body, "Add New Capability", size=14).pack(anchor="w")
        tk.Label(body, text="Register a new student service or technical skill", bg=Colors.SURFACE,
                 fg=Colors.TEXT_MUTED, font=font(9)).pack(anchor="w", pady=(0, 14))

        self.name_field = FormField(body, "Skill name", "e.g. React Frontend Development")
        self.name_field.pack(fill="x", pady=(0, 12))
        self.category_field = ComboField(body, "Skill category", SKILL_CATEGORIES, default=SKILL_CATEGORIES[0])
        self.category_field.pack(fill="x", pady=(0, 12))
        self.level_field = ComboField(body, "Proficiency level", SKILL_LEVELS, default="Advanced")
        self.level_field.pack(fill="x", pady=(0, 12))
        self.description_field = TextArea(
            body, "Description & details", height=4,
            placeholder="Describe what projects you can help with, what tools you know, or any previous projects.",
        )
        self.description_field.pack(fill="x", pady=(0, 12))

        self.status = FeedbackLabel(body, wraplength=360)
        self.status.pack(fill="x", pady=(0, 6))
        FlatButton(body, "⊕  Register Skill to Profile", self._register).pack(fill="x")
        self.name_field.entry.bind("<Return>", lambda _e: self._register())
        return card

    # ------------------------------------------------------------------
    def _register(self) -> None:
        name = self.name_field.value()
        description = self.description_field.value()
        existing = [s["name"] for s in self.store.get_skills(self.user["student_id"])]
        ok, message = validate_skill(name, description, existing)
        self.name_field.set_error(not ok and "Description" not in message)
        self.description_field.set_error(not ok and "Description" in message)
        if not ok:
            self.status.show_error(message)
            return
        level = self.level_field.value()
        self.store.add_skill(self.user["student_id"], name, self.category_field.value(), level, description)
        self.show(confirmed=f"'{name}' added to your profile!")

    def _delete(self, skill: dict) -> None:
        if messagebox.askyesno("Remove skill", f"Remove '{skill['name']}' from your profile?"):
            self.store.delete_skill(skill["skill_id"])
            self.show()
