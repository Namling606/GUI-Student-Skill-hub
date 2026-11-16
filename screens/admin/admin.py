"""Administrator panel (Figma frame: admin-screen) with an analytics dashboard."""

import tkinter as tk
from tkinter import filedialog, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import ICONS, Colors, font
from data.analytics import AnalyticsData
from screens.base import BaseScreen
from utils import charts
from utils.helpers import hours_ago_text
from widgets.components import (
    Card, ComboField, FlatButton, PlaceholderEntry, TabBar, clear_children, page_header, section_title,
    status_badge,
)

RANGE_OPTIONS = {"Last 3 months": 3, "Last 6 months": 6, "All 8 months": 8}
DIRECTORY_COLUMNS = [("NAME", 2), ("STUDENT ID", 2), ("CAMPUS EMAIL", 4), ("SKILLS", 2), ("STATUS", 2), ("ACTIONS", 3)]


class AdminScreen(BaseScreen):
    """Two tabs: 'Overview' (KPIs, directory, moderation) and 'Analytics' (charts)."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.analytics = AnalyticsData()

    def render(self, tab: str = "overview", range_label: str = "All 8 months", **_ignored) -> None:
        page_header(self.content, "Administrator Panel",
                    "Manage registered campus accounts, monitor talent trading activity, and inspect flagged materials.")
        TabBar(self.content, [("overview", "Overview"), ("analytics", "Analytics")], tab,
               lambda key: self.show(tab=key, range_label=range_label)).pack(fill="x", pady=(0, 18))
        self._render_data_notice()
        if tab == "analytics":
            self._render_analytics(range_label)
        else:
            self._render_overview()

    def _render_data_notice(self) -> None:
        notice = tk.Frame(self.content, bg=Colors.PRIMARY_LIGHT, highlightthickness=1,
                          highlightbackground=Colors.PRIMARY_LIGHT_HOVER)
        notice.pack(fill="x", pady=(0, 16))
        marker = tk.Frame(notice, bg=Colors.PRIMARY, width=4)
        marker.pack(side="left", fill="y")
        copy = tk.Frame(notice, bg=Colors.PRIMARY_LIGHT)
        copy.pack(side="left", fill="x", expand=True, padx=14, pady=10)
        tk.Label(copy, text="DEMO ANALYTICS", bg=Colors.PRIMARY_LIGHT, fg=Colors.PRIMARY,
                 font=font(8, "bold")).pack(anchor="w")
        student_count = len(self.store.directory())
        tk.Label(
            copy,
            text=f"Statistics use generated sample data (1,420 students); the live directory currently has "
                 f"{student_count} student accounts.",
            bg=Colors.PRIMARY_LIGHT, fg=Colors.TEXT_MUTED, font=font(9), anchor="w",
        ).pack(anchor="w", pady=(2, 0))

    # ==================================================================
    # Overview tab
    # ==================================================================
    def _render_overview(self) -> None:
        self._build_kpis()
        columns = tk.Frame(self.content, bg=Colors.BG)
        columns.pack(fill="x", pady=(18, 0))
        columns.columnconfigure(0, weight=3, uniform="admin")
        columns.columnconfigure(1, weight=2, uniform="admin")
        self._build_directory(columns).grid(row=0, column=0, sticky="new", padx=(0, 12))
        self.moderation_holder = tk.Frame(columns, bg=Colors.BG)
        self.moderation_holder.grid(row=0, column=1, sticky="new", padx=(12, 0))
        self._render_moderation()

    def _build_kpis(self) -> None:
        kpis = self.analytics.kpis()
        flags = len(self.store.open_reports())
        cards = [
            ("Total Students", f"{kpis['total_students']:,}", f"↑ {kpis['term_growth']}% this term", Colors.TEXT_LIGHT, False),
            ("Active Trade Offers", f"{kpis['active_offers']:,}", f"↑ {kpis['offers_change']}% this week", Colors.TEXT_LIGHT, False),
            ("Skills Listed", f"{kpis['skills_listed']:,}", f"Average {kpis['skills_per_student']} per student", Colors.TEXT_LIGHT, False),
            ("Reported Content", f"{flags} Flags", "Needs immediate review" if flags else "All clear", Colors.DANGER, True),
        ]
        accents = [Colors.PRIMARY, Colors.SUCCESS, Colors.WARNING, Colors.DANGER]
        row = tk.Frame(self.content, bg=Colors.BG)
        row.pack(fill="x")
        row.columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")
        for index, (label, value, note, note_color, alert) in enumerate(cards):
            card = Card(row, padding=(18, 16))
            if alert:
                card.configure(highlightbackground=Colors.DANGER, highlightcolor=Colors.DANGER)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0 if index == 3 else 8))
            tk.Frame(card.body, bg=accents[index], height=3).pack(fill="x", pady=(0, 12))
            top = tk.Frame(card.body, bg=Colors.SURFACE)
            top.pack(fill="x")
            tk.Label(top, text=label, bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(9)).pack(side="left")
            bubble_bg, bubble_fg = (Colors.DANGER_LIGHT, Colors.DANGER) if alert else (Colors.PRIMARY_LIGHT, Colors.PRIMARY)
            tk.Label(top, text=ICONS["admin"] if alert else "∿", bg=bubble_bg, fg=bubble_fg, font=font(11), width=3,
                     pady=2).pack(side="right")
            tk.Label(card.body, text=value, bg=Colors.SURFACE, fg=Colors.TEXT, font=font(18, "bold"), anchor="w").pack(fill="x", pady=(8, 0))
            tk.Label(card.body, text=note, bg=Colors.SURFACE, fg=note_color, font=font(8, "bold" if alert else "normal"),
                     anchor="w").pack(fill="x")

    # ------------------------------------------------------------------
    # Student directory
    # ------------------------------------------------------------------
    def _build_directory(self, parent) -> Card:
        card = Card(parent, padding=(20, 18))
        header = tk.Frame(card.body, bg=Colors.SURFACE)
        header.pack(fill="x", pady=(0, 12))
        section_title(header, "Registered Student Directory").pack(side="left")
        FlatButton(header, "Export CSV", self._export_csv, "secondary", size=9).pack(side="right")
        box = tk.Frame(header, bg=Colors.SURFACE, highlightthickness=1, highlightbackground=Colors.BORDER)
        box.pack(side="right", padx=10)
        self.filter_entry = PlaceholderEntry(box, placeholder="Filter by name or ID…", width=18)
        self.filter_entry.pack(padx=8, pady=6)
        self.filter_entry.bind("<KeyRelease>", lambda _e: self._render_rows())

        self.table = tk.Frame(card.body, bg=Colors.SURFACE)
        self.table.pack(fill="x")
        for col, (_title, weight) in enumerate(DIRECTORY_COLUMNS):
            self.table.columnconfigure(col, weight=weight)
        self._render_rows()
        return card

    def _render_rows(self) -> None:
        clear_children(self.table)
        for col, (title, _weight) in enumerate(DIRECTORY_COLUMNS):
            tk.Label(self.table, text=title, bg=Colors.BG, fg=Colors.TEXT_MUTED, font=font(8, "bold"),
                     anchor="w", padx=8, pady=8).grid(row=0, column=col, sticky="ew")
        directory = self.store.directory(self.filter_entry.value())
        if directory.empty:
            tk.Label(self.table, text="No students match this filter.", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED,
                     font=font(10), pady=16).grid(row=1, column=0, columnspan=len(DIRECTORY_COLUMNS))
            return
        for index, record in enumerate(directory.to_dict("records"), start=1):
            cells = [(record["full_name"], True), (record["student_id"], False), (record["email"], False),
                     (f"{record['skills_count']} registered", False)]
            for col, (text, bold) in enumerate(cells):
                color = Colors.PRIMARY if col == 3 else (Colors.TEXT if bold else Colors.TEXT_MUTED)
                tk.Label(self.table, text=text, bg=Colors.SURFACE, fg=color, anchor="w", padx=8, pady=9,
                         font=font(9, "bold" if bold or col == 3 else "normal")).grid(row=index, column=col, sticky="ew")
            badge_cell = tk.Frame(self.table, bg=Colors.SURFACE)
            badge_cell.grid(row=index, column=4, sticky="w", padx=8)
            status_badge(badge_cell, record["status"]).pack()
            actions = tk.Frame(self.table, bg=Colors.SURFACE)
            actions.grid(row=index, column=5, sticky="w")
            sid, suspended = record["student_id"], record["status"] == "Suspended"
            FlatButton(actions, "View", lambda s=sid: self._view_student(s), "secondary", size=8, padx=10, pady=4).pack(side="left")
            FlatButton(actions, "Reactivate" if suspended else "Suspend", lambda s=sid, st=suspended: self._toggle_suspend(s, st),
                       "soft" if suspended else "secondary", size=8, padx=10, pady=4).pack(side="left", padx=4)

    def _view_student(self, student_id: str) -> None:
        student = self.store.get_student(student_id)
        skills = ", ".join(s["name"] for s in self.store.get_skills(student_id)) or "None"
        messagebox.showinfo(
            student["full_name"],
            f"Student ID: {student['student_id']}\nEmail: {student['email']}\nCourse: {student['course']}\n"
            f"Status: {student['status']}\nRating: {student['rating']:.1f} ({int(student['review_count'])} reviews)\n"
            f"Skills: {skills}",
        )

    def _toggle_suspend(self, student_id: str, is_suspended: bool) -> None:
        name = self.store.get_student(student_id)["full_name"]
        action = "reactivate" if is_suspended else "suspend"
        if messagebox.askyesno("Confirm", f"Are you sure you want to {action} {name}'s account?"):
            self.store.set_student_status(student_id, "Active" if is_suspended else "Suspended")
            self._render_rows()

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(title="Export student directory", defaultextension=".csv",
                                            initialfile="student_directory.csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            self.store.directory(self.filter_entry.value()).to_csv(path, index=False)
        except OSError as exc:
            messagebox.showerror("Export failed", f"The file could not be saved:\n{exc}")
            return
        messagebox.showinfo("Export complete", f"Student directory saved to:\n{path}")

    # ------------------------------------------------------------------
    # Content moderation
    # ------------------------------------------------------------------
    def _render_moderation(self) -> None:
        clear_children(self.moderation_holder)
        card = Card(self.moderation_holder, padding=(20, 18))
        card.pack(fill="x")
        section_title(card.body, "Content Moderation").pack(anchor="w", pady=(0, 12))
        reports = self.store.open_reports()
        if not reports:
            tk.Label(card.body, text="No flagged content. Great job!", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED,
                     font=font(10)).pack(anchor="w", pady=8)
        for report in reports:
            self._build_report(card.body, report)

    def _build_report(self, parent, report: dict) -> None:
        box = tk.Frame(parent, bg=Colors.DANGER_LIGHT, highlightthickness=1, highlightbackground=Colors.DANGER_LIGHT_HOVER)
        box.pack(fill="x", pady=(0, 10))
        inner = tk.Frame(box, bg=Colors.DANGER_LIGHT)
        inner.pack(fill="x", padx=12, pady=10)
        top = tk.Frame(inner, bg=Colors.DANGER_LIGHT)
        top.pack(fill="x")
        tk.Label(top, text=f"Flagged {report['target_type']}", bg=Colors.DANGER_LIGHT, fg=Colors.DANGER, font=font(9, "bold")).pack(side="left")
        tk.Label(top, text=hours_ago_text(int(report["hours_ago"])), bg=Colors.DANGER_LIGHT, fg=Colors.TEXT_LIGHT, font=font(8)).pack(side="right")
        tk.Label(inner, text=f"Title: \"{report['title']}\"", bg=Colors.DANGER_LIGHT, fg=Colors.TEXT, font=font(9, "bold"),
                 anchor="w", wraplength=300, justify="left").pack(fill="x", pady=(4, 0))
        tk.Label(inner, text=f"Reported for: {report['reason']}", bg=Colors.DANGER_LIGHT, fg=Colors.TEXT_MUTED, font=font(8),
                 anchor="w", wraplength=300, justify="left").pack(fill="x", pady=(2, 8))
        buttons = tk.Frame(inner, bg=Colors.DANGER_LIGHT)
        buttons.pack(anchor="w")
        rid = report["report_id"]
        FlatButton(buttons, "Take Down", lambda: self._resolve(rid, True), "danger", size=9, padx=12, pady=5).pack(side="left")
        FlatButton(buttons, "Dismiss", lambda: self._resolve(rid, False), "secondary", size=9, padx=12, pady=5).pack(side="left", padx=8)

    def _resolve(self, report_id: int, take_down: bool) -> None:
        question = "Take down this content?" if take_down else "Dismiss this report?"
        if not messagebox.askyesno("Confirm", question):
            return
        self.store.resolve_report(report_id, take_down)
        self.show(tab="overview")  # refreshes KPI flag count, directory and moderation list

    # ==================================================================
    # Analytics tab
    # ==================================================================
    def _render_analytics(self, range_label: str) -> None:
        months = RANGE_OPTIONS.get(range_label, 8)
        monthly = self.analytics.monthly_window(months)

        top = tk.Frame(self.content, bg=Colors.BG)
        top.pack(fill="x", pady=(0, 14))
        section_title(top, "Platform Analytics", bg=Colors.BG, size=14).pack(side="left")
        picker = ComboField(top, "", list(RANGE_OPTIONS), default=range_label, bg=Colors.BG)
        picker.pack(side="right", ipadx=20)
        picker.on_change(lambda: self.show(tab="analytics", range_label=picker.value()))
        tk.Label(top, text="Time range:", bg=Colors.BG, fg=Colors.TEXT_MUTED, font=font(9)).pack(side="right", padx=8)

        self._build_summary(months)
        grid = tk.Frame(self.content, bg=Colors.BG)
        grid.pack(fill="x", pady=(14, 0))
        grid.columnconfigure((0, 1), weight=1, uniform="charts")
        figures = [
            charts.registrations_chart(monthly), charts.requests_chart(monthly),
            charts.categories_chart(self.analytics.categories), charts.courses_chart(self.analytics.courses),
            charts.ratings_chart(self.analytics.ratings), charts.top_skills_chart(self.analytics.top_skills),
        ]
        for index, figure in enumerate(figures):
            card = Card(grid, padding=(8, 8))
            card.grid(row=index // 2, column=index % 2, sticky="nsew", pady=(0, 14),
                      padx=(0 if index % 2 == 0 else 7, 0 if index % 2 == 1 else 7))
            canvas = FigureCanvasTkAgg(figure, master=card.body)
            widget = canvas.get_tk_widget()
            widget.configure(height=290)
            widget.pack(fill="both", expand=True)
            canvas.draw()

    def _build_summary(self, months: int) -> None:
        summary = self.analytics.summary(months)
        items = [
            ("New students", f"{summary['new_students']:,}"),
            ("Request completion rate", f"{summary['completion_rate']}%"),
            ("Average review rating", f"{summary['average_rating']:.2f} ★"),
            ("Peak sign-up month", summary["peak_month"]),
        ]
        row = tk.Frame(self.content, bg=Colors.BG)
        row.pack(fill="x")
        row.columnconfigure((0, 1, 2, 3), weight=1, uniform="summary")
        for index, (label, value) in enumerate(items):
            card = Card(row, padding=(16, 12))
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0 if index == 3 else 8))
            tk.Label(card.body, text=label, bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(9),
                     anchor="w").pack(fill="x")
            tk.Label(card.body, text=value, bg=Colors.SURFACE, fg=Colors.PRIMARY, font=font(15, "bold"),
                     anchor="w").pack(fill="x")
