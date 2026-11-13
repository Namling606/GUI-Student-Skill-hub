"""Skill requests (Figma frames: skill-request-screen, both tabs)."""

import tkinter as tk
from tkinter import messagebox

from config import STATUS_ACCEPTED, STATUS_COMPLETED, STATUS_DECLINED, STATUS_PENDING, Colors, font
from screens.base import BaseScreen
from utils.helpers import days_ago_text
from widgets.components import Avatar, Card, FlatButton, TabBar, page_header, section_title, status_badge


class RequestsScreen(BaseScreen):
    """Incoming and sent requests with accept / decline / complete actions."""

    def render(self, tab: str = "incoming", **_ignored) -> None:
        uid = self.user["student_id"]
        incoming, sent = self.store.incoming_requests(uid), self.store.sent_requests(uid)
        page_header(self.content, "Skill Requests",
                    "Track skill trade offers from other campus peers and view outstanding requests you made.")
        tabs = [("incoming", f"Incoming Requests ({len(incoming)})"), ("sent", f"My Sent Requests ({len(sent)})")]
        TabBar(self.content, tabs, tab, lambda key: self.show(tab=key)).pack(fill="x", pady=(0, 18))

        columns = tk.Frame(self.content, bg=Colors.BG)
        columns.pack(fill="x")
        columns.columnconfigure(0, weight=3, uniform="req")
        columns.columnconfigure(1, weight=1, uniform="req")
        listing = tk.Frame(columns, bg=Colors.BG)
        listing.grid(row=0, column=0, sticky="new", padx=(0, 12))
        records = incoming if tab == "incoming" else sent
        if not records:
            tk.Label(listing, text="Nothing here yet.", bg=Colors.BG, fg=Colors.TEXT_MUTED, font=font(10)).pack(anchor="w")
        for record in records:
            self._build_request_card(listing, record, tab == "incoming").pack(fill="x", pady=(0, 14))
        self._build_tracking(columns, sent).grid(row=0, column=1, sticky="new", padx=(12, 0))

    # ------------------------------------------------------------------
    def _build_request_card(self, parent, record: dict, is_incoming: bool) -> Card:
        card = Card(parent, padding=(22, 18))
        top = tk.Frame(card.body, bg=Colors.SURFACE)
        top.pack(fill="x")
        Avatar(top, record["other_name"], size=40).pack(side="left")
        texts = tk.Frame(top, bg=Colors.SURFACE)
        texts.pack(side="left", padx=12)
        tk.Label(texts, text=record["other_name"], bg=Colors.SURFACE, fg=Colors.TEXT, font=font(11, "bold")).pack(anchor="w")
        tk.Label(texts, text=f"{record['skill']} • Requested {days_ago_text(record['days_ago'])}", bg=Colors.SURFACE,
                 fg=Colors.TEXT_MUTED, font=font(9)).pack(anchor="w")
        status_badge(top, record["status"]).pack(side="right", anchor="n")

        tk.Label(card.body, text=f"\"{record['message']}\"", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(10),
                 wraplength=560, justify="left", anchor="w").pack(fill="x", pady=(12, 0))

        if is_incoming and record["status"] == STATUS_PENDING:
            buttons = tk.Frame(card.body, bg=Colors.SURFACE)
            buttons.pack(anchor="w", pady=(14, 0))
            FlatButton(buttons, "⊕  Accept Request", lambda: self._set_status(record, STATUS_ACCEPTED)).pack(side="left")
            FlatButton(buttons, "Decline", lambda: self._decline(record), "secondary").pack(side="left", padx=10)
        elif is_incoming and record["status"] == STATUS_ACCEPTED:
            FlatButton(card.body, "Mark as Completed", lambda: self._set_status(record, STATUS_COMPLETED), "soft").pack(
                anchor="w", pady=(14, 0))
        return card

    def _build_tracking(self, parent, sent: list) -> Card:
        card = Card(parent, padding=(20, 18))
        section_title(card.body, "Sent Requests Tracking").pack(anchor="w", pady=(0, 12))
        for record in sent:
            row = tk.Frame(card.body, bg=Colors.SURFACE, highlightthickness=1, highlightbackground=Colors.BORDER)
            row.pack(fill="x", pady=4)
            texts = tk.Frame(row, bg=Colors.SURFACE)
            texts.pack(side="left", padx=10, pady=8)
            tk.Label(texts, text=f"To {record['other_name']}", bg=Colors.SURFACE, fg=Colors.TEXT, font=font(9, "bold")).pack(anchor="w")
            tk.Label(texts, text=record["skill"], bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(8)).pack(anchor="w")
            status_badge(row, record["status"]).pack(side="right", padx=10)
        FlatButton(card.body, "Initiate Peer Request", lambda: self.navigate("search"), "soft", size=9).pack(anchor="w", pady=(12, 0))
        return card

    # ------------------------------------------------------------------
    def _set_status(self, record: dict, status: str) -> None:
        self.store.update_request_status(record["request_id"], status)
        self.show(tab=self.params.get("tab", "incoming"))

    def _decline(self, record: dict) -> None:
        if messagebox.askyesno("Decline request", f"Decline {record['other_name']}'s request for '{record['skill']}'?"):
            self._set_status(record, STATUS_DECLINED)
