"""Central configuration: design tokens (colours, fonts) and app constants.
"""

import sys

# ----------------------------------------------------------------------------
# Application constants
# ----------------------------------------------------------------------------
APP_TITLE = "StudentSkill Hub"
WINDOW_SIZE = "1280x780"
MIN_WINDOW_SIZE = (1100, 700)
SIDEBAR_WIDTH = 230
TOPBAR_HEIGHT = 60
INSTITUTION_BADGE = "SCE"
EMAIL_DOMAIN = "rub.edu.bt"

SKILL_CATEGORIES = [
    "Tech & Coding",
    "Design & Arts",
    "Media Production",
    "Academics & Tutoring",
    "Music",
    "Writing & Languages",
]
SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]
# Default proficiency estimate (%) assigned when a skill level is chosen.
LEVEL_TO_PERCENT = {"Beginner": 35, "Intermediate": 60, "Advanced": 85, "Expert": 95}

# Request / report statuses
STATUS_PENDING = "Pending"
STATUS_ACCEPTED = "Accepted"
STATUS_DECLINED = "Declined"
STATUS_COMPLETED = "Completed"


# ----------------------------------------------------------------------------
# Colours (taken from the Figma file)
# ----------------------------------------------------------------------------
class Colors:
    PRIMARY = "#4F46E5"
    PRIMARY_HOVER = "#4338CA"
    PRIMARY_LIGHT = "#EEF2FF"
    PRIMARY_LIGHT_HOVER = "#E0E7FF"

    BG = "#F6F7FB"
    AUTH_BG = "#EEF2FF"
    SURFACE = "#FFFFFF"
    BORDER = "#E4E7F0"

    TEXT = "#0F172A"
    TEXT_MUTED = "#64748B"
    TEXT_LIGHT = "#94A3B8"
    TEXT_ON_PRIMARY = "#FFFFFF"

    DANGER = "#DC2626"
    DANGER_HOVER = "#B91C1C"
    DANGER_LIGHT = "#FEE2E2"
    DANGER_LIGHT_HOVER = "#FECACA"

    SUCCESS = "#059669"
    SUCCESS_LIGHT = "#D1FAE5"
    SUCCESS_SOLID = "#22C55E"
    WARNING = "#D97706"
    WARNING_LIGHT = "#FEF3C7"
    STAR = "#F59E0B"


# Status name -> (text colour, background colour)
STATUS_STYLES = {
    STATUS_PENDING: (Colors.WARNING, Colors.WARNING_LIGHT),
    STATUS_ACCEPTED: (Colors.SUCCESS, Colors.SUCCESS_LIGHT),
    STATUS_DECLINED: (Colors.DANGER, Colors.DANGER_LIGHT),
    STATUS_COMPLETED: (Colors.PRIMARY, Colors.PRIMARY_LIGHT),
    "Active": (Colors.SUCCESS, Colors.SUCCESS_LIGHT),
    "Suspended": (Colors.DANGER, Colors.DANGER_LIGHT),
}

# Palette used for initial-based avatars
AVATAR_COLORS = [
    "#4F46E5", "#7C3AED", "#DB2777", "#EA580C",
    "#059669", "#0891B2", "#CA8A04", "#4F46E5",
]


# ----------------------------------------------------------------------------
# Fonts
# ----------------------------------------------------------------------------
if sys.platform.startswith("win"):
    FONT_FAMILY = "Segoe UI"
elif sys.platform == "darwin":
    FONT_FAMILY = "Helvetica Neue"
else:
    FONT_FAMILY = "DejaVu Sans"


def font(size: int = 10, weight: str = "normal", italic: bool = False) -> tuple:
    """Return a Tk font tuple using the app's font family."""
    style = weight + (" italic" if italic else "")
    return (FONT_FAMILY, size, style.strip())


# Text glyphs used as icons (kept as constants so they can be swapped easily)
ICONS = {
    "logo": "\U0001F393",  # graduation cap
    "dashboard": "▣",
    "profile": "☺",
    "skills": "✪",
    "search": "⌕",
    "portfolio": "▤",
    "requests": "✉",
    "feedback": "✎",
    "admin": "⚑",
    "logout": "⇥",
    "plus": "+",
    "delete": "✕",
    "send": "➤",
    "upload": "⇪",
    "star_full": "★",
    "star_empty": "☆",
}
