"""Input validation helpers.

Every single-field validator returns a ``(is_valid, message)`` tuple so
screens can show the message directly to the user. Form-level validators
(``validate_registration`` / ``validate_profile`` / ``validate_login``)
return a ``{field_name: message}`` dictionary so each offending field can
be highlighted.
"""

import re

from config import EMAIL_DOMAIN

_EMAIL_PATTERN = re.compile(rf"^[A-Za-z0-9._%+-]+@{re.escape(EMAIL_DOMAIN)}$")
_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,59}$")
_NAME_INPUT_PATTERN = re.compile(r"^[A-Za-z .'-]*$")
_STUDENT_ID_PATTERN = re.compile(r"^\d{8}$")
_STUDENT_ID_INPUT_PATTERN = re.compile(r"^\d*$")
_SKILL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 &+#./'-]{1,39}$")

Result = tuple  # (bool, str)


def _ok() -> Result:
    return True, ""


# ----------------------------------------------------------------------------
# Single-field validators
# ----------------------------------------------------------------------------
def validate_full_name(value: str) -> Result:
    value = value.strip()
    if not value:
        return False, "Full name is required."
    if not _NAME_PATTERN.match(value):
        return False, "Full name must be 2-60 letters (spaces, . ' - allowed)."
    return _ok()


def is_name_input(value: str) -> bool:
    """Allow only the characters accepted in a full name while the user types."""
    return bool(_NAME_INPUT_PATTERN.fullmatch(value))


def is_student_id_input(value: str) -> bool:
    """Allow only digits in a student ID while the user types."""
    return bool(_STUDENT_ID_INPUT_PATTERN.fullmatch(value))


def validate_student_id(value: str) -> Result:
    value = value.strip()
    if not value:
        return False, "Student ID is required."
    if not _STUDENT_ID_PATTERN.match(value):
        return False, "Student ID must be exactly 8 digits (e.g. 08230177)."
    return _ok()


def validate_campus_email(value: str) -> Result:
    value = value.strip()
    if not value:
        return False, "Campus email is required."
    if not _EMAIL_PATTERN.match(value):
        return False, f"Use your campus email (name@{EMAIL_DOMAIN})."
    return _ok()


def validate_course(value: str) -> Result:
    value = value.strip()
    if not value:
        return False, "Course / class is required."
    if len(value) < 2 or len(value) > 60:
        return False, "Course / class must be 2-60 characters."
    return _ok()


def validate_password(value: str) -> Result:
    if not value:
        return False, "Password is required."
    if len(value) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        return False, "Password must contain both letters and numbers."
    return _ok()


def validate_password_match(password: str, confirm: str) -> Result:
    if not confirm:
        return False, "Please confirm your password."
    if password != confirm:
        return False, "Passwords do not match."
    return _ok()


# ----------------------------------------------------------------------------
# Form-level validators
# ----------------------------------------------------------------------------
def validate_login(identifier: str, password: str) -> dict:
    """Basic presence checks for the login form."""
    errors = {}
    if not identifier.strip():
        errors["identifier"] = "Enter your username or student email."
    if not password:
        errors["password"] = "Enter your password."
    return errors


def validate_registration(form: dict) -> dict:
    """Validate the registration form. Returns ``{field: message}`` errors."""
    checks = {
        "full_name": validate_full_name(form["full_name"]),
        "student_id": validate_student_id(form["student_id"]),
        "email": validate_campus_email(form["email"]),
        "course": validate_course(form["course"]),
        "password": validate_password(form["password"]),
        "confirm": validate_password_match(form["password"], form["confirm"]),
    }
    return {field: msg for field, (ok, msg) in checks.items() if not ok}


def validate_profile(name: str, email: str, course: str, bio: str) -> dict:
    checks = {
        "full_name": validate_full_name(name),
        "email": validate_campus_email(email),
        "course": validate_course(course),
    }
    errors = {field: msg for field, (ok, msg) in checks.items() if not ok}
    if len(bio.strip()) > 400:
        errors["bio"] = "Biography must be 400 characters or fewer."
    return errors


# ----------------------------------------------------------------------------
# Feature-specific validators
# ----------------------------------------------------------------------------
def validate_skill(name: str, description: str, existing_names: list) -> Result:
    name = name.strip()
    if not name:
        return False, "Skill name is required."
    if not _SKILL_NAME_PATTERN.match(name):
        return False, "Skill name must be 2-40 characters (letters, numbers, & + # . / ' -)."
    if name.lower() in (n.lower() for n in existing_names):
        return False, "You have already registered this skill."
    if len(description.strip()) > 300:
        return False, "Description must be 300 characters or fewer."
    return _ok()


def validate_achievement(text: str) -> Result:
    text = text.strip()
    if not text:
        return False, "Achievement cannot be empty."
    if len(text) > 100:
        return False, "Achievement must be 100 characters or fewer."
    return _ok()


def validate_portfolio_item(title: str, tag: str) -> Result:
    title = title.strip()
    if not title:
        return False, "Title is required."
    if len(title) < 3 or len(title) > 50:
        return False, "Title must be 3-50 characters."
    if not tag.strip():
        return False, "Please choose a skill tag."
    return _ok()


def validate_request_message(skill: str, message: str) -> Result:
    if not skill.strip():
        return False, "Please choose the skill you need help with."
    message = message.strip()
    if len(message) < 10:
        return False, "Please describe what you need (at least 10 characters)."
    if len(message) > 300:
        return False, "Message must be 300 characters or fewer."
    return _ok()


def validate_feedback(collaboration: str, rating: int, review: str) -> Result:
    if not collaboration.strip():
        return False, "Select a completed collaboration to review."
    if rating < 1:
        return False, "Please choose a star rating (1-5)."
    review = review.strip()
    if len(review) < 10:
        return False, "Please write a short review (at least 10 characters)."
    if len(review) > 300:
        return False, "Review must be 300 characters or fewer."
    return _ok()
