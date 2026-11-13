"""Login and registration screen (Figma frame: login-register)."""

import tkinter as tk
from tkinter import messagebox

from config import APP_TITLE, EMAIL_DOMAIN, ICONS, Colors, font
from utils.validators import (
    is_name_input, is_student_id_input, validate_campus_email, validate_course, validate_full_name,
    validate_login, validate_password, validate_password_match, validate_registration, validate_student_id,
)
from widgets.components import Card, FeedbackLabel, FlatButton, FormField, LinkLabel
from widgets.dialogs import ask_text

# Values shown in the Figma prototype - prefilled to make demos quick.
DEMO_STUDENT_ID = "08230188.sce@rub.edu.bt"
DEMO_STUDENT_PASSWORD = "Dorji@123456"
DEMO_ADMIN_ID = f"admin@{EMAIL_DOMAIN}"

FAQ_TEXT = (
    "How do I register?\nUse the 'Create Student Account' form with your 8-digit student ID "
    f"and your campus email (name@{EMAIL_DOMAIN}).\n\n"
    "How do I find help?\nOpen Search, look for a skill and press 'Request Help'.\n\n"
    "How do I offer my skills?\nAdd them under Skills and showcase your work in Portfolio.\n\n"
    "Who are administrators?\nThey keep the hub safe by reviewing reported content."
)

REGISTER_FIELD_ORDER = ["full_name", "student_id", "email", "course", "password", "confirm"]


class AuthScreen(tk.Frame):
    """Welcome header with a sign-in card and a student registration card."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=Colors.AUTH_BG)
        self.app = app
        self.store = app.store
        self.admin_mode = False
        self._build()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build(self) -> None:
        center = tk.Frame(self, bg=Colors.AUTH_BG)
        center.place(relx=0.5, rely=0.5, anchor="center")
        self._build_welcome(center)

        cards = tk.Frame(center, bg=Colors.AUTH_BG)
        cards.pack(pady=(26, 0))
        self._build_login_card(cards)
        self._build_register_card(cards)

    def _build_welcome(self, parent) -> None:
        logo = tk.Canvas(parent, width=54, height=54, bg=Colors.AUTH_BG, highlightthickness=0)
        logo.pack()
        logo.create_oval(0, 0, 54, 54, fill=Colors.PRIMARY, outline=Colors.PRIMARY)
        logo.create_text(27, 27, text=ICONS["logo"], font=font(22), fill="white")
        tk.Label(parent, text=APP_TITLE, bg=Colors.AUTH_BG, fg=Colors.TEXT, font=font(22, "bold")).pack(pady=(10, 2))
        tk.Label(parent, text="The ultimate skills marketplace and talent showcase for university students",
                 bg=Colors.AUTH_BG, fg=Colors.TEXT_MUTED, font=font(10)).pack()

    def _build_login_card(self, parent) -> None:
        card = Card(parent, padding=(30, 28))
        card.grid(row=0, column=0, padx=14, sticky="n")
        body = card.body
        tk.Frame(body, width=400, height=1, bg=Colors.SURFACE).pack()  # fixes the card width

        self.login_title = tk.Label(body, text="Welcome Back", bg=Colors.SURFACE, fg=Colors.TEXT,
                                    font=font(15, "bold"), anchor="w")
        self.login_title.pack(fill="x")
        self.login_subtitle = tk.Label(body, text="Sign in to search student skills and projects",
                                       bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(9), anchor="w")
        self.login_subtitle.pack(fill="x", pady=(0, 16))

        self.login_id = FormField(body, "Username or student email", "e.g. 08230177.sce@rub.edu.bt")
        self.login_id.pack(fill="x", pady=(0, 12))
        self.login_pw = FormField(body, "Password", "Enter your password", show="•")
        self.login_pw.pack(fill="x")
        self._set_demo_credentials()

        self.show_pw_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            body, text="Show password", variable=self.show_pw_var, command=self._toggle_password,
            bg=Colors.SURFACE, activebackground=Colors.SURFACE, fg=Colors.TEXT_MUTED,
            selectcolor=Colors.SURFACE, font=font(9), bd=0, highlightthickness=0, cursor="hand2",
        ).pack(anchor="w", pady=(6, 0))

        self.login_status = FeedbackLabel(body, wraplength=400)
        self.login_status.pack(fill="x", pady=(4, 6))
        self.login_button = FlatButton(body, "Sign In to Campus Hub", self._login)
        self.login_button.pack(fill="x")

        self.admin_link = LinkLabel(body, "Sign In as Admin", self._toggle_admin_mode, color="#4F46E5", size=10)
        self.admin_link.pack(anchor="w", pady=(16, 14))

        footer = tk.Frame(body, bg=Colors.SURFACE)
        footer.pack(fill="x")
        LinkLabel(footer, "Forgot Password?", self._forgot_password).pack(side="left")
        LinkLabel(footer, "FAQ", self._show_faq).pack(side="right")
        tk.Label(footer, text="Need help? ", bg=Colors.SURFACE, fg=Colors.TEXT_MUTED, font=font(9)).pack(side="right")

        for field in (self.login_id, self.login_pw):
            field.entry.bind("<Return>", lambda _e: self._login())

    def _build_register_card(self, parent) -> None:
        card = Card(parent, padding=(30, 28))
        card.grid(row=0, column=1, padx=14, sticky="n")
        body = card.body
        tk.Frame(body, width=400, height=1, bg=Colors.SURFACE).pack()

        tk.Label(body, text="Create Student Account", bg=Colors.SURFACE, fg=Colors.TEXT,
                 font=font(15, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text="Join your peers in showcasing skills and finding help", bg=Colors.SURFACE,
                 fg=Colors.TEXT_MUTED, font=font(9), anchor="w").pack(fill="x", pady=(0, 16))

        grid = tk.Frame(body, bg=Colors.SURFACE)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="reg")
        specs = {
            "full_name": ("Full name", "e.g. Dorji Tshomo", ""),
            "student_id": ("Student ID", "e.g. 08230177", ""),
            "email": ("Campus email", f"e.g. 08230177.sce@{EMAIL_DOMAIN}", ""),
            "course": ("Course / class", "e.g. B.Ed English/History", ""),
            "password": ("Password", "Min. 8 characters", "•"),
            "confirm": ("Confirm password", "Match password", "•"),
        }
        self.reg_fields = {}
        self._register_error_field = None
        for index, key in enumerate(REGISTER_FIELD_ORDER):
            label, placeholder, show = specs[key]
            field_options = {}
            if key == "full_name":
                field_options = {
                    "input_validator": is_name_input,
                    "invalid_input_callback": lambda: self._show_register_field_error(
                        "full_name", "Use letters, spaces, apostrophes, periods, or hyphens in a name."
                    ),
                }
            elif key == "student_id":
                field_options = {
                    "input_validator": is_student_id_input,
                    "invalid_input_callback": lambda: self._show_register_field_error(
                        "student_id", "Student ID can contain digits only."
                    ),
                }
            field = FormField(grid, label, placeholder, show=show, **field_options)
            field.grid(row=index // 2, column=index % 2, sticky="ew",
                       padx=(0, 8) if index % 2 == 0 else (8, 0), pady=(0, 12))
            self.reg_fields[key] = field

        self.register_status = FeedbackLabel(body, wraplength=400)
        self.register_status.pack(fill="x", pady=(0, 6))
        FlatButton(body, "Register Account", self._register).pack(fill="x")
        self._register_last_values = {key: field.raw_value() for key, field in self.reg_fields.items()}
        for key, field in self.reg_fields.items():
            field.entry.bind("<FocusOut>", lambda _e, field_key=key: self._validate_register_field(field_key),
                             add="+")
            field.entry.bind("<KeyRelease>", lambda _e, field_key=key: self._register_field_changed(field_key),
                             add="+")

    # ------------------------------------------------------------------
    # Login behaviour
    # ------------------------------------------------------------------
    def _set_demo_credentials(self) -> None:
        self.login_id.set_value(DEMO_STUDENT_ID)
        self.login_pw.set_value(DEMO_STUDENT_PASSWORD)

    def _toggle_password(self) -> None:
        self.login_pw.set_masked(not self.show_pw_var.get())

    def _toggle_admin_mode(self) -> None:
        """Switch the sign-in card between student and administrator mode."""
        self.admin_mode = not self.admin_mode
        self.login_status.clear()
        self.login_id.set_error(False)
        self.login_pw.set_error(False)
        if self.admin_mode:
            self.login_title.configure(text="Administrator Sign In")
            self.login_subtitle.configure(text="Restricted area - enter your administrator credentials")
            self.login_button.set_text("Sign In to Admin Panel")
            self.admin_link.configure(text="Back to Student Sign In")
            self.login_id.set_value(DEMO_ADMIN_ID)
            self.login_pw.set_value("")
        else:
            self.login_title.configure(text="Welcome Back")
            self.login_subtitle.configure(text="Sign in to search student skills and projects")
            self.login_button.set_text("Sign In to Campus Hub")
            self.admin_link.configure(text="Sign In as Admin")
            self._set_demo_credentials()

    def _login(self) -> None:
        identifier, password = self.login_id.value(), self.login_pw.raw_value()
        errors = validate_login(identifier, password)
        self.login_id.set_error("identifier" in errors)
        self.login_pw.set_error("password" in errors)
        if errors:
            self.login_status.show_error(next(iter(errors.values())))
            return
        user, message = self.store.authenticate(identifier, password, as_admin=self.admin_mode)
        if user is None:
            self.login_pw.set_error(True)
            self.login_status.show_error(message)
            return
        self.login_status.clear()
        self.app.login(user)

    def _show_register_field_error(self, key: str, message: str) -> None:
        self._register_error_field = key
        self.reg_fields[key].set_error(True, message)
        self.register_status.clear()

    def _register_field_validator(self, key: str):
        if key == "full_name":
            return validate_full_name(self.reg_fields[key].value())
        if key == "student_id":
            return validate_student_id(self.reg_fields[key].value())
        if key == "email":
            return validate_campus_email(self.reg_fields[key].value())
        if key == "course":
            return validate_course(self.reg_fields[key].value())
        if key == "password":
            return validate_password(self.reg_fields[key].raw_value())
        return validate_password_match(
            self.reg_fields["password"].raw_value(), self.reg_fields["confirm"].raw_value()
        )

    def _validate_register_field(self, key: str) -> None:
        ok, message = self._register_field_validator(key)
        self.reg_fields[key].set_error(not ok, message if not ok else "")
        if not ok:
            self._show_register_field_error(key, message)
        elif self._register_error_field == key:
            self._register_error_field = None

    def _register_field_changed(self, key: str) -> None:
        value = self.reg_fields[key].raw_value()
        changed = value != self._register_last_values[key]
        self._register_last_values[key] = value
        if changed and self._register_error_field == key:
            self._validate_register_field(key)

    def _forgot_password(self) -> None:
        email = ask_text(self, "Reset password", "Campus email", validate_campus_email,
                         placeholder=f"name@{EMAIL_DOMAIN}", ok_text="Send reset link")
        if email is None:
            return
        if self.store.reset_password(email):
            messagebox.showinfo("Reset link sent", f"A password reset link was sent to {email}.\n(Demo only - no email is really sent.)")
        else:
            messagebox.showerror("Not found", "No account is registered with that email.")

    @staticmethod
    def _show_faq() -> None:
        messagebox.showinfo("Frequently asked questions", FAQ_TEXT)

    # ------------------------------------------------------------------
    # Registration behaviour
    # ------------------------------------------------------------------
    def _register(self) -> None:
        form = {
            "full_name": self.reg_fields["full_name"].value(),
            "student_id": self.reg_fields["student_id"].value(),
            "email": self.reg_fields["email"].value(),
            "course": self.reg_fields["course"].value(),
            "password": self.reg_fields["password"].raw_value(),
            "confirm": self.reg_fields["confirm"].raw_value(),
        }
        errors = validate_registration(form)
        for key, field in self.reg_fields.items():
            field.set_error(key in errors, errors.get(key, ""))
        if errors:
            self.register_status.clear()
            first_key = next(key for key in REGISTER_FIELD_ORDER if key in errors)
            self._register_error_field = first_key
            self.reg_fields[first_key].focus()
            return
        try:
            self.store.register_student(form)
        except ValueError as exc:
            self.register_status.show_error(str(exc))
            return
        self.register_status.clear()
        self._register_error_field = None
        messagebox.showinfo("Account created", f"Welcome, {form['full_name']}! You can now sign in.")
        if self.admin_mode:
            self._toggle_admin_mode()
        self.login_id.set_value(form["email"])
        self.login_pw.set_value(form["password"])
        for field in self.reg_fields.values():
            field.clear()

    def reset(self) -> None:
        """Return the screen to its initial state (called after logout)."""
        self.admin_mode = True  # force the toggle below to switch back to student mode
        self._toggle_admin_mode()
        self.login_status.clear()
        self.register_status.clear()
