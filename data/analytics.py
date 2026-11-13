"""Static, campus-wide analytics data for the admin dashboard.

The numbers are generated with numpy using a fixed random seed, so the
analytics are realistic yet identical on every run. ``multinomial`` is used
so the generated series add up exactly to the headline totals shown on the
admin panel (1,420 students, 5,821 listed skills, ...).
"""

import numpy as np
import pandas as pd

from config import SKILL_CATEGORIES

TOTAL_STUDENTS = 1420
TOTAL_SKILLS_LISTED = 5821
ACTIVE_TRADE_OFFERS = 382
ACTIVE_OFFERS_WEEKLY_CHANGE = 8  # percent, shown as a static trend note

MONTHS = ["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
COURSES = ["Computer Science", "Information Systems", "Education", "Design & Arts", "Media Studies", "Mathematics"]
TOP_SKILL_NAMES = [
    "Web Development", "Graphic Design", "Photography", "Tutoring",
    "Video Editing", "Python", "Copywriting", "Music",
]


class AnalyticsData:
    """Generates and serves the pandas DataFrames used by the analytics charts."""

    def __init__(self, seed: int = 42):
        rng = np.random.default_rng(seed)
        self.monthly = self._build_monthly(rng)
        self.categories = self._build_categories(rng)
        self.courses = self._build_courses(rng)
        self.ratings = self._build_ratings(rng)
        self.top_skills = self._build_top_skills(rng)

    # ------------------------------------------------------------------
    # Table builders
    # ------------------------------------------------------------------
    @staticmethod
    def _build_monthly(rng) -> pd.DataFrame:
        weights = np.array([10, 11, 12, 12, 13, 14, 14, 14], dtype=float)
        signups = rng.multinomial(TOTAL_STUDENTS, weights / weights.sum())
        requests = (signups * 0.30 + rng.integers(18, 40, size=len(MONTHS))).astype(int)
        completed = (requests * rng.uniform(0.55, 0.80, size=len(MONTHS))).astype(int)
        return pd.DataFrame({
            "month": MONTHS,
            "signups": signups,
            "requests": requests,
            "completed": completed,
            "total_students": signups.cumsum(),
        })

    @staticmethod
    def _build_categories(rng) -> pd.DataFrame:
        weights = np.array([30, 24, 12, 14, 8, 12], dtype=float)
        counts = rng.multinomial(TOTAL_SKILLS_LISTED, weights / weights.sum())
        return pd.DataFrame({"category": SKILL_CATEGORIES, "skills": counts})

    @staticmethod
    def _build_courses(rng) -> pd.DataFrame:
        weights = np.array([26, 18, 22, 12, 11, 11], dtype=float)
        counts = rng.multinomial(TOTAL_STUDENTS, weights / weights.sum())
        return pd.DataFrame({"course": COURSES, "students": counts})

    @staticmethod
    def _build_ratings(rng) -> pd.DataFrame:
        weights = np.array([0.02, 0.03, 0.08, 0.27, 0.60])
        counts = rng.multinomial(900, weights)
        return pd.DataFrame({"stars": [1, 2, 3, 4, 5], "reviews": counts})

    @staticmethod
    def _build_top_skills(rng) -> pd.DataFrame:
        counts = np.sort(rng.integers(45, 170, size=len(TOP_SKILL_NAMES)))[::-1]
        return pd.DataFrame({"skill": TOP_SKILL_NAMES, "requests": counts})

    # ------------------------------------------------------------------
    # Queries used by the admin screen
    # ------------------------------------------------------------------
    def monthly_window(self, months: int) -> pd.DataFrame:
        """Return the most recent ``months`` rows of the monthly table."""
        return self.monthly.tail(months).reset_index(drop=True)

    def term_growth_percent(self) -> int:
        """Sign-up growth: last three months compared with the three before."""
        signups = self.monthly["signups"].to_numpy()
        previous = signups[-6:-3].sum()
        return int(round(100 * (signups[-3:].sum() / previous - 1))) if previous else 0

    def kpis(self) -> dict:
        """Headline numbers for the admin stat cards."""
        total_students = int(self.monthly["signups"].sum())
        skills = int(self.categories["skills"].sum())
        return {
            "total_students": total_students,
            "term_growth": self.term_growth_percent(),
            "active_offers": ACTIVE_TRADE_OFFERS,
            "offers_change": ACTIVE_OFFERS_WEEKLY_CHANGE,
            "skills_listed": skills,
            "skills_per_student": round(skills / total_students, 1),
        }

    def summary(self, months: int) -> dict:
        """Quick insights shown above the charts for the selected window."""
        window = self.monthly_window(months)
        requests = int(window["requests"].sum())
        completed = int(window["completed"].sum())
        weights = self.ratings["stars"] * self.ratings["reviews"]
        peak = window.loc[window["signups"].idxmax()]
        return {
            "new_students": int(window["signups"].sum()),
            "completion_rate": round(100 * completed / requests) if requests else 0,
            "average_rating": round(float(weights.sum() / self.ratings["reviews"].sum()), 2),
            "peak_month": f"{peak['month']} ({int(peak['signups'])})",
        }
