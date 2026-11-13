"""Main application window: owns the data, the signed-in user and navigation."""

import tkinter as tk

from config import APP_TITLE, MIN_WINDOW_SIZE, WINDOW_SIZE, Colors
from data.store import ROLE_ADMIN, DataStore
from screens.admin import AdminScreen
from screens.auth import AuthScreen
from screens.student.dashboard import DashboardScreen
from screens.student.feedback import FeedbackScreen
from screens.student.portfolio import PortfolioScreen
from screens.student.profile import ProfileScreen
from screens.student.requests import RequestsScreen
from screens.student.search import SearchScreen
from screens.student.skills import SkillsScreen
from widgets.components import bind_mousewheel, setup_styles
from widgets.shell import Sidebar, Topbar

# (key, sidebar label, icon key, highlighted-as-danger)
STUDENT_NAV = [
    ("dashboard", "Dashboard", "dashboard", False),
    ("profile", "Profile", "profile", False),
    ("skills", "Skills", "skills", False),
    ("search", "Search", "search", False),
    ("portfolio", "Portfolio", "portfolio", False),
    ("requests", "Requests", "requests", False),
    ("feedback", "Feedback", "feedback", False),
]
ADMIN_NAV = [("admin", "Admin Panel", "admin", True)]

STUDENT_SCREENS = {
    "dashboard": DashboardScreen, "profile": ProfileScreen, "skills": SkillsScreen,
    "search": SearchScreen, "portfolio": PortfolioScreen, "requests": RequestsScreen,
    "feedback": FeedbackScreen,
}
ADMIN_SCREENS = {"admin": AdminScreen}


class App(tk.Tk):
    """Switches between the sign-in screen and the signed-in application shell."""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(*MIN_WINDOW_SIZE)
        self.configure(bg=Colors.BG)
        setup_styles(self)
        bind_mousewheel(self)

        self.store = DataStore()
        self.user = None
        self.shell = None
        self.screens = {}
        self.current_key = None

        self.auth_screen = AuthScreen(self, self)
        self.show_auth()

    # ------------------------------------------------------------------
    # Session handling
    # ------------------------------------------------------------------
    def show_auth(self) -> None:
        self.auth_screen.reset()
        self.auth_screen.pack(fill="both", expand=True)

    def login(self, user: dict) -> None:
        """Open the application shell for a signed-in student or administrator."""
        self.user = user
        self.auth_screen.pack_forget()
        is_admin = user["role"] == ROLE_ADMIN
        nav, registry = (ADMIN_NAV, ADMIN_SCREENS) if is_admin else (STUDENT_NAV, STUDENT_SCREENS)

        self.shell = tk.Frame(self, bg=Colors.BG)
        self.shell.pack(fill="both", expand=True)
        self.sidebar = Sidebar(self.shell, nav, self.navigate, self.logout, admin_mode=is_admin)
        self.sidebar.pack(side="left", fill="y")
        main = tk.Frame(self.shell, bg=Colors.BG)
        main.pack(side="left", fill="both", expand=True)
        self.topbar = Topbar(main, user, admin_mode=is_admin)
        self.topbar.pack(fill="x")
        self.content_area = tk.Frame(main, bg=Colors.BG)
        self.content_area.pack(fill="both", expand=True)

        self.screens = {key: cls(self.content_area, self) for key, cls in registry.items()}
        self.navigate(nav[0][0])

    def logout(self) -> None:
        self.shell.destroy()
        self.shell, self.screens, self.user, self.current_key = None, {}, None, None
        self.show_auth()

    def refresh_user(self) -> None:
        """Reload the signed-in user's record (after a profile change)."""
        self.user = self.store.get_student(self.user["student_id"])
        self.topbar.update_user(self.user)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def navigate(self, key: str, **params) -> None:
        """Show the screen registered under ``key`` and highlight it in the sidebar."""
        if self.current_key in self.screens:
            self.screens[self.current_key].pack_forget()
        screen = self.screens[key]
        screen.pack(fill="both", expand=True)
        screen.show(**params)
        self.sidebar.set_active(key)
        self.current_key = key
