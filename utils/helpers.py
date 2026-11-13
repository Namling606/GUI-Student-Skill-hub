"""Small, reusable helper functions that are not tied to any screen."""


def initials(name: str) -> str:
    """Return up to two upper-case initials for a name ('Pema Zangmo' -> 'PZ')."""
    parts = [p for p in name.replace(".", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def first_name(name: str) -> str:
    """Return the first word of a full name."""
    parts = name.split()
    return parts[0] if parts else name


def days_ago_text(days: int) -> str:
    """Convert a number of days into friendly text ('today', '3 days ago', ...)."""
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    months = max(1, days // 30)
    return f"{months} month{'s' if months > 1 else ''} ago"


def hours_ago_text(hours: int) -> str:
    """Convert hours into friendly text ('3 hrs ago')."""
    if hours < 1:
        return "just now"
    if hours == 1:
        return "1 hr ago"
    if hours < 24:
        return f"{hours} hrs ago"
    return days_ago_text(hours // 24)


def truncate(text: str, limit: int) -> str:
    """Shorten text to ``limit`` characters, adding an ellipsis when cut."""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def avatar_color_for(key: str, palette: list) -> str:
    """Pick a stable colour from ``palette`` for any string key."""
    return palette[sum(ord(ch) for ch in str(key)) % len(palette)]
