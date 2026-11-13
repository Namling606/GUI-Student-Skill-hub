"""Student dashboard (Figma frame: dashboard-home)."""

import tkinter as tk

from config import ICONS, Colors, font
from screens.base import BaseScreen
from utils.helpers import days_ago_text, first_name, truncate
from widgets.components import (
    Avatar, Card, FlatButton, LinkLabel, StarLabel, make_clickable, page_header,
    section_title, status_badge,
)


class DashboardScreen(BaseScreen):
    """Welcome banner, statistics, recent requests, ratings and quick actions."""

    def render(self, **params) -> None:
        user = self.user
        page_header(
            self.content, f"Welcome back, {first_name(user['full_name'])}!",
            "Explore campus skill-sharing requests, manage your showcases, and assist your peers today.",
        )
        self._render_stats()

        columns = tk.Frame(self.content, bg=Colors.BG)
        columns.pack(fill="x", pady=(18, 0))
        columns.columnconfigure(0, weight=3, uniform="dash")
        columns.columnconfigure(1, weight=2, uniform="dash")
        self._render_recent_requests(columns).grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        self._render_ratings(columns).grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self._render_quick_actions()

    # ------------------------------------------------------------------
    def _render_stats(self) -> None:
        uid = self.user["student_id"]
        stats = [
            ("My Registered Skills", f"{len(self.store.get_skills(uid))} Active", "skills",
             Colors.PRIMARY_LIGHT, Colors.PRIMARY, "skills"),
            ("Portfolio Showcases", f"{len(self.store.get_portfolio(uid))} Assets", "portfolio",
             Colors.PRIMARY_LIGHT, Colors.PRIMARY, "portfolio"),
            ("Active Trade Requests", f"{self.store.count_pending_incoming(uid)} Pending", "requests",
             Colors.WARNING_LIGHT, Colors.WARNING, "requests"),
            ("Completed Collaborations", f"{int(self.user['collab_count'])} Success", "feedback",
             Colors.SUCCESS_LIGHT, Colors.SUCCESS, "feedback"),
        ]
        row = tk.Frame(self.content, bg=Colors.BG)
        row.pack(fill="x")
        row.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")
        for index, (label, value, icon, bubble_bg, bubble_fg, target) in enumerate(stats):
            card = Card(row, padding=(18, 16))
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0 if index == 3 else 8))
            top = tk.Frame(card.body, bg=Colors.SURFACE)
            top.pack(fill="x")
            tk.Label(top, text=label, bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(9)).pack(side="left")
            tk.Label(top, text=ICONS[icon], bg=bubble_bg, fg=bubble_fg, font=font(11), width=3,
                     pady=3).pack(side="right")
            tk.Label(card.body, text=value, bg=Colors.SURFACE, fg=Colors.TEXT, font=font(18, "bold"),
                     anchor="w").pack(fill="x", pady=(10, 0))
            make_clickable(card, lambda t=target: self.navigate(t))

    def _render_recent_requests(self, parent) -> Card:
        card = Card(parent, padding=(22, 20))
        header = tk.Frame(card.body, bg=Colors.SURFACE)
        header.pack(fill="x", pady=(0, 12))
        section_title(header, "Recent Skill Requests").pack(side="left")
        LinkLabel(header, "View Inbox", lambda: self.navigate("requests")).pack(side="right")

        requests = self.store.incoming_requests(self.user["student_id"])[:3]
        if not requests:
            tk.Label(card.body, text="No skill requests yet.", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED,
                     font=font(10)).pack(anchor="w", pady=12)
        for request in requests:
            row = tk.Frame(card.body, bg=Colors.SURFACE, highlightthickness=1, highlightbackground=Colors.BORDER)
            row.pack(fill="x", pady=4)
            Avatar(row, request["other_name"], size=34).pack(side="left", padx=(12, 10), pady=10)
            texts = tk.Frame(row, bg=Colors.SURFACE)
            texts.pack(side="left")
            tk.Label(texts, text=request["other_name"], bg=Colors.SURFACE, fg=Colors.TEXT,
                     font=font(10, "bold")).pack(anchor="w")
            tk.Label(texts, text=f"{request['skill']} • {days_ago_text(request['days_ago']).capitalize()}",
                     bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(8)).pack(anchor="w")
            status_badge(row, request["status"]).pack(side="right", padx=12)
        return card

    def _render_ratings(self, parent) -> Card:
        user = self.user
        card = Card(parent, padding=(22, 20))
        section_title(card.body, "My Ratings & Reviews").pack(anchor="w", pady=(0, 12))

        summary = tk.Frame(card.body, bg=Colors.PRIMARY_LIGHT)
        summary.pack(fill="x")
        tk.Label(summary, text=f"{user['rating']:.1f}", bg=Colors.PRIMARY_LIGHT, fg=Colors.PRIMARY,
                 font=font(26, "bold")).pack(side="left", padx=(16, 12), pady=14)
        texts = tk.Frame(summary, bg=Colors.PRIMARY_LIGHT)
        texts.pack(side="left")
        StarLabel(texts, user["rating"], size=12, bg=Colors.PRIMARY_LIGHT).pack(anchor="w")
        tk.Label(texts, text=f"Based on {int(user['review_count'])} student reviews", bg=Colors.PRIMARY_LIGHT,
                 fg=Colors.TEXT_MUTED, font=font(8)).pack(anchor="w")

        for feedback in self.store.feedback_received(user["student_id"])[:2]:
            item = tk.Frame(card.body, bg=Colors.SURFACE, highlightthickness=1, highlightbackground=Colors.BORDER)
            item.pack(fill="x", pady=(8, 0))
            top = tk.Frame(item, bg=Colors.SURFACE)
            top.pack(fill="x", padx=8, pady=(6, 0))
            tk.Label(top, text=feedback["from_name"], bg=Colors.SURFACE, fg=Colors.TEXT,
                     font=font(9, "bold")).pack(side="left")
            tk.Label(top, text=feedback["skill"], bg=Colors.SURFACE, fg=Colors.TEXT_LIGHT,
                     font=font(8)).pack(side="right")
            tk.Label(item, text=f"\"{truncate(feedback['comment'], 90)}\"", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED,
                     font=font(9, italic=True), wraplength=300, justify="left", anchor="w").pack(
                fill="x", padx=8, pady=(2, 8))
        return card

    def _render_quick_actions(self) -> None:
        tk.Label(self.content, text="Quick Actions", bg=Colors.BG, fg=Colors.TEXT, font=font(12, "bold"),
                 anchor="w").pack(fill="x", pady=(26, 10))
        row = tk.Frame(self.content, bg=Colors.BG)
        row.pack(anchor="w")
        FlatButton(row, f"{ICONS['plus']}  Add New Skill", lambda: self.navigate("skills"), "primary").pack(side="left")
        FlatButton(row, f"{ICONS['upload']}  Upload Portfolio Asset",
                   lambda: self.navigate("portfolio", upload=True), "soft").pack(side="left", padx=10)
        FlatButton(row, f"{ICONS['search']}  Search Peer Skills", lambda: self.navigate("search"),
                   "secondary").pack(side="left")
