"""Find student talent (Figma frames: search-screen and its variants)."""

import tkinter as tk

from config import ICONS, SKILL_CATEGORIES, Colors, font
from data.store import ALL_CATEGORIES
from screens.base import BaseScreen
from utils.validators import validate_request_message
from widgets.components import (
    Avatar, Card, ComboField, FeedbackLabel, FlatButton, Pill, PlaceholderEntry, TextArea, banner_panel,
    page_header,
)
from widgets.dialogs import ask_choice

REPORT_REASONS = [
    "Inappropriate content", "Spam or misleading information", "Harassment or bullying",
    "Plagiarism / copyright", "Other",
]
SEARCH_PLACEHOLDER = "Search for 'Web Development', 'Design', 'Math'..."


class SearchScreen(BaseScreen):
    """Search bar + result cards, with detail, request and confirmation views.

    The ``mode`` parameter selects the view: ``list`` (default), ``detail``,
    ``request``, ``submitted`` or ``reported``.
    """

    def render(self, mode: str = "list", student_id: str = "", query: str = "",
               category: str = ALL_CATEGORIES, **_ignored) -> None:
        self.query, self.category = query, category
        page_header(self.content, "Find Student Talent",
                    "Search skills across the university campus to find peers for collaborations, tutoring, or club project assistance.")
        self._build_search_bar()

        results = self.store.search_students(query, category, exclude_id=self.user["student_id"], limit=12)
        featured = not query and category == ALL_CATEGORIES
        heading = "Featured campus talent results" if featured else "Search results"
        if mode == "list":
            heading = f"{heading} ({len(results)} found)"
        tk.Label(self.content, text=heading, bg=Colors.BG, fg=Colors.TEXT, font=font(11, "bold"),
                 anchor="w").pack(fill="x", pady=(20, 10))

        if mode == "list":
            self._build_results(results)
        else:
            student = self.store.get_student(student_id)
            if mode == "detail":
                self._build_detail(student)
            elif mode == "request":
                self._build_request_form(student)
            elif mode == "submitted":
                self._build_confirmation(student, "➤  Your request has been submitted!", Colors.SUCCESS_SOLID)
            elif mode == "reported":
                self._build_confirmation(student, "➤  Report Successful!", "#CC0C0C")

    # ------------------------------------------------------------------
    # Search bar
    # ------------------------------------------------------------------
    def _build_search_bar(self) -> None:
        card = Card(self.content, padding=(16, 10))
        card.pack(fill="x")
        row = tk.Frame(card.body, bg=Colors.SURFACE)
        row.pack(fill="x")
        tk.Label(row, text=ICONS["search"], bg=Colors.SURFACE, fg=Colors.PRIMARY, font=font(14)).pack(side="left", padx=(0, 10))
        self.search_entry = PlaceholderEntry(row, placeholder=SEARCH_PLACEHOLDER)
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=6)
        if self.query:
            self.search_entry.set_value(self.query)
        tk.Frame(row, width=1, bg=Colors.BORDER).pack(side="left", fill="y", padx=14, pady=2)
        self.category_combo = ComboField(row, "", [ALL_CATEGORIES] + SKILL_CATEGORIES, default=self.category)
        self.category_combo.pack(side="left", padx=(0, 12), ipadx=30)
        FlatButton(row, "Search Hub", self._search).pack(side="left")
        self.search_entry.bind("<Return>", lambda _e: self._search())

    def _search(self) -> None:
        query = self.search_entry.value().strip()
        if len(query) > 60:
            query = query[:60]
        self.show(mode="list", query=query, category=self.category_combo.value())

    # ------------------------------------------------------------------
    # Result list
    # ------------------------------------------------------------------
    def _build_results(self, results: list) -> None:
        if not results:
            card = Card(self.content, padding=(24, 30))
            card.pack(fill="x")
            tk.Label(card.body, text="No students match your search. Try another skill or category.",
                     bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(10)).pack()
            return
        grid = tk.Frame(self.content, bg=Colors.BG)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1, 2), weight=1, uniform="results")
        for index, student in enumerate(results):
            card = self._build_student_card(grid, student)
            card.grid(row=index // 3, column=index % 3, sticky="nsew", pady=(0, 14),
                      padx=(0 if index % 3 == 0 else 7, 0 if index % 3 == 2 else 7))

    def _build_student_card(self, parent, student: dict) -> Card:
        card = Card(parent, padding=(18, 16))
        top = tk.Frame(card.body, bg=Colors.SURFACE)
        top.pack(fill="x")
        Avatar(top, student["full_name"], size=44, photo_path=student["photo_path"]).pack(side="left")
        texts = tk.Frame(top, bg=Colors.SURFACE)
        texts.pack(side="left", padx=12)
        tk.Label(texts, text=student["full_name"], bg=Colors.SURFACE, fg=Colors.TEXT, font=font(11, "bold")).pack(anchor="w")
        tk.Label(texts, text=f"★ {student['rating']:.1f}", bg=Colors.SURFACE, fg=Colors.STAR, font=font(9, "bold")).pack(anchor="w")
        self._skill_chips(card.body, student["top_skills"])

        buttons = tk.Frame(card.body, bg=Colors.SURFACE)
        buttons.pack(fill="x", pady=(14, 0))
        buttons.columnconfigure((0, 1), weight=1, uniform="cardbtn")
        sid = student["student_id"]
        FlatButton(buttons, "View Profile", lambda: self._open("detail", sid), "secondary", size=9).grid(
            row=0, column=0, sticky="ew", padx=(0, 4))
        FlatButton(buttons, f"{ICONS['send']}  Request Help", lambda: self._open("request", sid), "primary", size=9).grid(
            row=0, column=1, sticky="ew", padx=(4, 0))
        return card

    @staticmethod
    def _skill_chips(parent, skills: list) -> None:
        tk.Label(parent, text="TOP SKILLS", bg=Colors.SURFACE, fg=Colors.TEXT_LIGHT, font=font(8, "bold"),
                 anchor="w").pack(fill="x", pady=(14, 6))
        chips = tk.Frame(parent, bg=Colors.SURFACE)
        chips.pack(fill="x")
        for skill in skills:
            Pill(chips, skill, size=8).pack(side="left", padx=(0, 5))

    def _open(self, mode: str, student_id: str) -> None:
        self.show(mode=mode, student_id=student_id, query=self.query, category=self.category)

    def _back_to_results(self) -> None:
        self.show(mode="list", query=self.query, category=self.category)

    # ------------------------------------------------------------------
    # Detail / request / confirmation views
    # ------------------------------------------------------------------
    def _student_header(self, body, student: dict) -> None:
        top = tk.Frame(body, bg=Colors.SURFACE)
        top.pack(fill="x")
        Avatar(top, student["full_name"], size=48, photo_path=student["photo_path"]).pack(side="left")
        texts = tk.Frame(top, bg=Colors.SURFACE)
        texts.pack(side="left", padx=12)
        tk.Label(texts, text=student["full_name"], bg=Colors.SURFACE, fg=Colors.TEXT, font=font(12, "bold")).pack(anchor="w")
        tk.Label(texts, text=f"★ {student['rating']:.1f}  •  {student['course']}", bg=Colors.SURFACE,
                 fg=Colors.TEXT_MUTED, font=font(9)).pack(anchor="w")
        self._skill_chips(body, self.store.top_skills(student["student_id"]))

    def _build_detail(self, student: dict) -> None:
        card = Card(self.content, padding=(24, 22))
        card.pack(fill="x")
        body = card.body
        self._student_header(body, student)
        sections = [("Description", student["bio"]), ("Experience", student["experience"]),
                    ("Recent Activities", student["recent_activity"])]
        for title, text in sections:
            tk.Label(body, text=title, bg=Colors.SURFACE, fg=Colors.TEXT, font=font(11, "bold"),
                     anchor="w").pack(fill="x", pady=(16, 2))
            tk.Label(body, text=text or "Nothing added yet.", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED,
                     font=font(10), wraplength=900, justify="left", anchor="w").pack(fill="x")
        sid = student["student_id"]
        FlatButton(body, f"{ICONS['send']}  Request Help", lambda: self._open("request", sid)).pack(fill="x", pady=(20, 8))
        FlatButton(body, f"{ICONS['send']}  Report", lambda: self._report(student), "danger").pack(fill="x")
        FlatButton(self.content, "◀  Back to results", self._back_to_results, "secondary").pack(anchor="w", pady=(16, 0))

    def _build_request_form(self, student: dict) -> None:
        card = Card(self.content, padding=(24, 22))
        card.pack(fill="x")
        body = card.body
        self._student_header(body, student)
        tk.Label(body, text=f"Request help from {student['full_name']}", bg=Colors.SURFACE, fg=Colors.TEXT,
                 font=font(12, "bold"), anchor="w").pack(fill="x", pady=(18, 10))

        skill_names = [s["name"] for s in self.store.get_skills(student["student_id"])]
        self.skill_combo = ComboField(body, "Skill you need help with", skill_names)
        self.skill_combo.pack(fill="x", pady=(0, 12))
        self.message_field = TextArea(body, "Message", height=5,
                                      placeholder="Describe what you need, how long it may take, and what you can offer in return.")
        self.message_field.pack(fill="x", pady=(0, 10))
        self.request_status = FeedbackLabel(body, wraplength=800)
        self.request_status.pack(fill="x", pady=(0, 8))

        buttons = tk.Frame(body, bg=Colors.SURFACE)
        buttons.pack(fill="x")
        FlatButton(buttons, f"{ICONS['send']}  Send Request", lambda: self._send_request(student), "primary").pack(side="right")
        FlatButton(buttons, "Cancel", self._back_to_results, "secondary").pack(side="right", padx=(0, 10))

    def _send_request(self, student: dict) -> None:
        skill, message = self.skill_combo.value(), self.message_field.value()
        ok, error = validate_request_message(skill, message)
        self.message_field.set_error(not ok)
        if not ok:
            self.request_status.show_error(error)
            return
        me, other = self.user["student_id"], student["student_id"]
        if self.store.has_pending_request(me, other, skill):
            self.request_status.show_error("You already have a pending request for this skill with this student.")
            return
        self.store.create_request(me, other, skill, message)
        self.show(mode="submitted", student_id=other, query=self.query, category=self.category)

    def _report(self, student: dict) -> None:
        reason = ask_choice(self, "Report student", "Reason for reporting", REPORT_REASONS, ok_text="Submit report")
        if reason is None:
            return
        self.store.create_report("Student", student["student_id"], f"Profile: {student['full_name']}",
                                 reason, self.user["student_id"])
        self.show(mode="reported", student_id=student["student_id"], query=self.query, category=self.category)

    def _build_confirmation(self, student: dict, message: str, color: str) -> None:
        card = Card(self.content, padding=(18, 16))
        card.pack(fill="x")
        self._skill_chips(card.body, self.store.top_skills(student["student_id"]))
        inner = banner_panel(card.body, message, color, self._back_to_results)
        inner.configure(bg=Colors.SURFACE)
        inner.pack(fill="x", pady=(12, 0))
