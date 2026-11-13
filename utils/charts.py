"""Matplotlib figure builders for the admin analytics page.

These functions are pure matplotlib (no Tkinter), which keeps chart code
separate from GUI code. The admin screen embeds the returned figures with
``FigureCanvasTkAgg``.
"""

from matplotlib.figure import Figure

from config import Colors

PALETTE = ["#2563EB", "#60A5FA", "#F59E0B", "#10B981", "#8B5CF6", "#EF4444"]
FIG_SIZE = (4.6, 3.0)
DPI = 100


def _new_axes(title: str):
    """Create a styled figure/axes pair shared by every chart."""
    fig = Figure(figsize=FIG_SIZE, dpi=DPI, facecolor=Colors.SURFACE, layout="constrained")
    ax = fig.add_subplot(111)
    ax.set_facecolor(Colors.SURFACE)
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold", color=Colors.TEXT)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(Colors.BORDER)
    ax.tick_params(colors=Colors.TEXT_MUTED, labelsize=8)
    ax.grid(axis="y", color=Colors.BORDER, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def registrations_chart(monthly) -> Figure:
    """Line chart: new student registrations per month."""
    fig, ax = _new_axes("New student registrations")
    ax.plot(monthly["month"], monthly["signups"], color=PALETTE[0], marker="o", linewidth=2)
    ax.fill_between(monthly["month"], monthly["signups"], color=PALETTE[0], alpha=0.12)
    for x, y in zip(monthly["month"], monthly["signups"]):
        ax.annotate(str(y), (x, y), textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=7, color=Colors.TEXT_MUTED)
    ax.set_ylim(0, monthly["signups"].max() * 1.25)
    return fig


def requests_chart(monthly) -> Figure:
    """Grouped bars: skill requests vs completed collaborations."""
    fig, ax = _new_axes("Requests vs completed collaborations")
    positions = range(len(monthly))
    width = 0.38
    ax.bar([p - width / 2 for p in positions], monthly["requests"], width,
           label="Requests", color=PALETTE[0])
    ax.bar([p + width / 2 for p in positions], monthly["completed"], width,
           label="Completed", color=PALETTE[3])
    ax.set_xticks(list(positions))
    ax.set_xticklabels(monthly["month"])
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    return fig


def categories_chart(categories) -> Figure:
    """Horizontal bars: listed skills per category."""
    fig, ax = _new_axes("Skills listed by category")
    data = categories.sort_values("skills")
    ax.barh(data["category"], data["skills"], color=PALETTE[1])
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=Colors.BORDER, linewidth=0.6)
    for y, value in enumerate(data["skills"]):
        ax.text(value, y, f" {value:,}", va="center", fontsize=7, color=Colors.TEXT_MUTED)
    ax.set_xlim(0, data["skills"].max() * 1.18)
    return fig


def courses_chart(courses) -> Figure:
    """Donut chart: students by course group."""
    fig, ax = _new_axes("Students by course group")
    ax.grid(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    wedges, _ = ax.pie(courses["students"], colors=PALETTE, startangle=90,
                       wedgeprops={"width": 0.42, "edgecolor": Colors.SURFACE})
    ax.legend(wedges, [f"{c} ({n})" for c, n in zip(courses["course"], courses["students"])],
              fontsize=7, frameon=False, loc="center left", bbox_to_anchor=(0.95, 0.5))
    return fig


def ratings_chart(ratings) -> Figure:
    """Bar chart: distribution of review star ratings."""
    fig, ax = _new_axes("Review rating distribution")
    ax.bar([f"{s}★" for s in ratings["stars"]], ratings["reviews"], color=PALETTE[2])
    for x, value in enumerate(ratings["reviews"]):
        ax.text(x, value, str(value), ha="center", va="bottom", fontsize=7, color=Colors.TEXT_MUTED)
    ax.set_ylim(0, ratings["reviews"].max() * 1.15)
    return fig


def top_skills_chart(top_skills) -> Figure:
    """Horizontal bars: most requested skills."""
    fig, ax = _new_axes("Most requested skills")
    data = top_skills.sort_values("requests")
    ax.barh(data["skill"], data["requests"], color=PALETTE[4])
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=Colors.BORDER, linewidth=0.6)
    ax.set_xlim(0, data["requests"].max() * 1.15)
    return fig


CHART_BUILDERS = {
    "registrations": registrations_chart,
    "requests": requests_chart,
    "categories": categories_chart,
    "courses": courses_chart,
    "ratings": ratings_chart,
    "top_skills": top_skills_chart,
}
