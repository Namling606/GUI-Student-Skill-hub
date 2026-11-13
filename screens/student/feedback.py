"""Ratings and feedback (Figma frame: rating-feedback-screen)."""

import tkinter as tk

from config import Colors, font
from screens.base import BaseScreen
from utils.helpers import days_ago_text
from utils.validators import validate_feedback
from widgets.components import (
    Card, ComboField, FeedbackLabel, FlatButton, Pill, StarLabel, StarPicker, TextArea, page_header, section_title,
)


class FeedbackScreen(BaseScreen):
    """Shows received reviews and lets the student review completed collaborations."""

    def render(self, notice: str = "", **_ignored) -> None:
        page_header(self.content, "Ratings & Feedback",
                    "Review what peers say about your collaborations, or submit constructive stars and reviews.")
        self._build_summary()

        columns = tk.Frame(self.content, bg=Colors.BG)
        columns.pack(fill="x", pady=(24, 0))
        columns.columnconfigure(0, weight=3, uniform="fb")
        columns.columnconfigure(1, weight=2, uniform="fb")
        self._build_received(columns).grid(row=0, column=0, sticky="new", padx=(0, 12))
        self._build_form(columns, notice).grid(row=0, column=1, sticky="new", padx=(12, 0))

    def _build_summary(self) -> None:
        user = self.user
        box = tk.Frame(self.content, bg=Colors.PRIMARY_LIGHT)
        box.pack(fill="x")
        tk.Label(box, text=f"{user['rating']:.1f}", bg=Colors.PRIMARY_LIGHT, fg=Colors.PRIMARY,
                 font=font(32, "bold")).pack(side="left", padx=(26, 16), pady=22)
        texts = tk.Frame(box, bg=Colors.PRIMARY_LIGHT)
        texts.pack(side="left")
        StarLabel(texts, user["rating"], size=16, bg=Colors.PRIMARY_LIGHT).pack(anchor="w")
        tk.Label(texts, text=f"Based on {int(user['review_count'])} registered campus collaborations",
                 bg=Colors.PRIMARY_LIGHT, fg=Colors.TEXT_MUTED, font=font(10, "bold")).pack(anchor="w")

    def _build_received(self, parent) -> tk.Frame:
        feedback = self.store.feedback_received(self.user["student_id"])
        holder = tk.Frame(parent, bg=Colors.BG)
        tk.Label(holder, text=f"Feedback I've Received ({len(feedback)})", bg=Colors.BG, fg=Colors.TEXT,
                 font=font(12, "bold"), anchor="w").pack(fill="x", pady=(0, 10))
        if not feedback:
            tk.Label(holder, text="No feedback yet. Complete a collaboration to receive your first review.",
                     bg=Colors.BG, fg=Colors.TEXT_MUTED, font=font(10), wraplength=480, justify="left").pack(anchor="w")
        for item in feedback:
            card = Card(holder, padding=(20, 16))
            card.pack(fill="x", pady=(0, 12))
            top = tk.Frame(card.body, bg=Colors.SURFACE)
            top.pack(fill="x")
            tk.Label(top, text=item["from_name"], bg=Colors.SURFACE, fg=Colors.TEXT, font=font(10, "bold")).pack(side="left")
            tk.Label(top, text=days_ago_text(item["days_ago"]), bg=Colors.SURFACE, fg=Colors.TEXT_LIGHT,
                     font=font(8)).pack(side="left", padx=8)
            Pill(top, item["skill"]).pack(side="right")
            StarLabel(card.body, item["rating"], size=12).pack(anchor="w", pady=(4, 4))
            tk.Label(card.body, text=f"\"{item['comment']}\"", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED,
                     font=font(10, italic=True), wraplength=520, justify="left", anchor="w").pack(fill="x")
        return holder

    def _build_form(self, parent, notice: str) -> Card:
        card = Card(parent, padding=(24, 22))
        body = card.body
        section_title(body, "Submit Peer Feedback", size=14).pack(anchor="w")
        tk.Label(body, text="Evaluate a completed student collaboration to help build trust on campus.",
                 bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(9), wraplength=360, justify="left").pack(anchor="w", pady=(2, 14))

        self.collaborations = self.store.reviewable_collaborations(self.user["student_id"])
        labels = [c["label"] for c in self.collaborations]
        self.collab_combo = ComboField(body, "Select completed collaboration", labels, default=labels[0] if labels else "")
        self.collab_combo.pack(fill="x", pady=(0, 14))

        tk.Label(body, text="OVERALL COLLABORATION RATING", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED,
                 font=font(8, "bold"), anchor="w").pack(fill="x", pady=(0, 4))
        stars_row = tk.Frame(body, bg=Colors.SURFACE)
        stars_row.pack(fill="x", pady=(0, 14))
        self.rating_text = tk.Label(stars_row, text="Select a rating", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(9))
        self.stars = StarPicker(stars_row, command=lambda n: self.rating_text.configure(text=f"{n} out of 5 stars"))
        self.stars.pack(side="left")
        self.rating_text.pack(side="left", padx=10)

        self.review_field = TextArea(
            body, "Written review & details", height=5,
            placeholder="Describe your experience. Did they communicate well? Were deliverables of high quality?")
        self.review_field.pack(fill="x", pady=(0, 10))

        self.status = FeedbackLabel(body, wraplength=360)
        self.status.pack(fill="x", pady=(0, 8))
        if notice:
            self.status.show_success(notice)
        if not self.collaborations:
            self.status.show_error("You have no completed collaborations waiting for a review.")
        self.submit_button = FlatButton(body, "Submit Peer Evaluation", self._submit)
        self.submit_button.pack(anchor="w")
        self.submit_button.set_enabled(bool(self.collaborations))
        return card

    def _submit(self) -> None:
        label = self.collab_combo.value()
        ok, message = validate_feedback(label, self.stars.value, self.review_field.value())
        self.review_field.set_error(not ok and message.startswith(("Please write", "Review must")))
        if not ok:
            self.status.show_error(message)
            return
        collaboration = next(c for c in self.collaborations if c["label"] == label)
        self.store.add_feedback(collaboration["request_id"], self.user["student_id"], collaboration["other_id"],
                                collaboration["skill"], self.stars.value, self.review_field.value())
        self.show(notice="Thank you! Your evaluation has been submitted.")
