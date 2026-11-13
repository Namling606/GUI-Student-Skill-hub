"""Static in-memory 'database' built from pandas DataFrames.

The tables mirror the ERD of the application:

    students ──< skills
    students ──< achievements
    students ──< portfolio
    students ──< requests (requester / provider)
    students ──< feedback (author / recipient)
    reports  >── (portfolio item or student)

Nothing is written to disk - the data lives for the duration of the program,
which is exactly what a prototype with static data needs.
"""

import pandas as pd

from config import (
    EMAIL_DOMAIN,
    LEVEL_TO_PERCENT,
    STATUS_ACCEPTED,
    STATUS_COMPLETED,
    STATUS_DECLINED,
    STATUS_PENDING,
)

ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"
ALL_CATEGORIES = "All Skill Categories"
DEFAULT_STUDENT_PASSWORD = "Student@123"

STUDENT_COLUMNS = [
    "student_id", "full_name", "email", "course", "year_label", "bio",
    "experience", "recent_activity", "rating", "review_count", "collab_count",
    "password", "status", "role", "photo_path",
]
SKILL_COLUMNS = ["skill_id", "student_id", "name", "category", "level", "proficiency", "description"]
ACHIEVEMENT_COLUMNS = ["achievement_id", "student_id", "text"]
PORTFOLIO_COLUMNS = ["item_id", "student_id", "title", "skill_tag", "days_ago", "color", "description", "image_path"]
REQUEST_COLUMNS = ["request_id", "from_id", "to_id", "skill", "message", "status", "days_ago"]
FEEDBACK_COLUMNS = ["feedback_id", "request_id", "from_id", "to_id", "skill", "rating", "comment", "days_ago"]
REPORT_COLUMNS = ["report_id", "target_type", "target_id", "title", "reason", "reporter_id", "hours_ago", "status"]


def _email_for(student_id: str) -> str:
    return f"{student_id}.sce@{EMAIL_DOMAIN}"


# ----------------------------------------------------------------------------
# Seed data
# ----------------------------------------------------------------------------
# (id, name, course, rating, reviews, collaborations, bio, experience, recent activity)
_STUDENT_SEED = [
    ("08230188", "Dorji", "B.Ed IT", 4.9, 14, 18,
     "Hi! I am a passionate UI/UX designer and hobbyist landscape photographer. "
     "When I'm not coding React apps, I help other students in typography, layout "
     "principles, and basic illustration.",
     "Designed posters and interfaces for campus events and tutored peers in typography.",
     "Building a design system for the Campus Computer Society."),
    ("08230101", "Pema Zangmo", "B.Ed English/History", 5.0, 22, 25,
     "A creative and passionate student with skills in photography, Adobe Lightroom, "
     "and portrait editing. Enjoys capturing natural moments and enhancing photographs "
     "through thoughtful composition, lighting, and professional editing.",
     "Has gained practical experience through personal photography projects, school "
     "events, and outdoor photo sessions. Worked on editing portraits using Lightroom, "
     "improving exposure, colors, and overall image quality.",
     "Recently focused on practicing portrait photography, experimenting with different "
     "lighting techniques, and editing a collection of photographs in Lightroom to build "
     "a personal portfolio."),
    ("08230102", "Tenzin Lhendup", "B.Sc Computer Science", 4.8, 17, 20,
     "Full-stack developer who enjoys building small web tools for student clubs.",
     "Built the club registration site and two hackathon prototypes using React and Node.",
     "Learning deployment pipelines and writing a beginner guide to REST APIs."),
    ("08230103", "Rinchen Dema", "B.Sc Mathematics", 4.9, 19, 24,
     "Patient peer tutor who makes calculus and algebra feel approachable.",
     "Two years of weekly tutoring sessions for first-year engineering students.",
     "Preparing a revision workbook for the upcoming mid-term exams."),
    ("08230104", "Tashi Pelden Dorji", "B.A Visual Arts", 4.7, 12, 15,
     "Illustrator and logo designer who loves clean, bold, minimal artwork.",
     "Designed logos for three student societies and a community fair.",
     "Experimenting with vector character design in Illustrator."),
    ("08230105", "Sonam Wangmo", "B.Ed Music", 5.0, 16, 21,
     "Pianist and music-theory tutor with a love for traditional and modern music.",
     "Performed at campus cultural nights and taught beginner piano lessons.",
     "Arranging a duet for the end-of-year concert."),
    ("08230106", "Yoezer Penjor", "B.A Dzongkha & English", 4.6, 11, 13,
     "Writer and editor who polishes essays, reports and creative pieces.",
     "Edited the student magazine and proofread several final-year dissertations.",
     "Drafting a short story collection and a style guide for the magazine."),
    ("08230107", "Choden", "B.Sc Information Systems", 4.5, 9, 10,
     "Database enthusiast who enjoys schema design and query tuning.",
     "Designed the database for a student club inventory system.",
     "Studying advanced SQL optimisation techniques."),
    ("08230108", "Tshering", "B.Sc Computer Science", 4.4, 8, 9,
     "Front-end learner who loves React and wants to pair on tricky bugs.",
     "Built a to-do app and a weather widget as course projects.",
     "Fixing state-management issues in a group project."),
    ("08230109", "Dema", "B.Ed Media Studies", 4.7, 13, 14,
     "Portrait and event photographer with a strong eye for natural light.",
     "Photographed campus events for the student union.",
     "Building a graduation portrait portfolio."),
    ("08230110", "Tshomo", "B.A Design", 4.6, 10, 12,
     "Prototype designer who turns rough ideas into clickable Figma flows.",
     "Created interactive prototypes for two startup pitch competitions.",
     "Exploring micro-interactions and accessibility in prototypes."),
    ("08230111", "Tobgay", "B.Ed Photography", 4.8, 12, 16,
     "Photographer who loves campus life, portraits and travel stories.",
     "Shot portraits and event coverage for the college newsletter.",
     "Editing a photo series on campus seasons."),
    ("08230112", "Jangchu", "B.Sc Computer Science", 4.3, 7, 8,
     "Web developer who enjoys React and helping classmates debug.",
     "Contributed to a class group project and a hackathon app.",
     "Learning TypeScript and testing."),
    ("08230113", "Zeedhen", "B.Sc Software Engineering", 4.6, 10, 11,
     "Backend developer comfortable with servers, APIs and databases.",
     "Maintained a small API for a student marketplace prototype.",
     "Setting up CI for a campus project."),
    ("08230114", "Leewang", "B.A English", 4.5, 8, 9,
     "Creative copywriter who crafts catchy posters, captions and speeches.",
     "Wrote copy for club recruitment drives and campus campaigns.",
     "Drafting a content calendar for a student society."),
    ("08230115", "Chimi", "B.Sc Information Systems", 4.2, 6, 6,
     "Spreadsheet and data-analysis tinkerer.",
     "Analysed survey data for a class research project.",
     "Learning pandas for data cleaning."),
    ("08230116", "Kuenga", "B.A Media & Culture", 4.0, 5, 5,
     "Video editor and tech-curious student.",
     "Edited short videos for student events.",
     "Practising colour grading."),
]

# student_id -> [(name, category, level, proficiency %, description)]
_SKILL_SEED = {
    "08230188": [
        ("Graphic Design", "Design & Arts", "Advanced", 90, "Posters, flyers, branding and layout design."),
        ("Python Programming", "Tech & Coding", "Advanced", 85, "Scripts, automation and small desktop apps."),
        ("Photography", "Design & Arts", "Intermediate", 60, "Landscape and campus event photography."),
        ("Video Editing", "Media Production", "Beginner", 35, "Basic cuts, transitions and captions."),
    ],
    "08230101": [("Photography", "Design & Arts", "Expert", 98, "Portrait and event photography."),
                 ("Lightroom", "Media Production", "Advanced", 92, "Colour grading and retouching."),
                 ("Portrait Editing", "Media Production", "Advanced", 90, "Skin retouching and tone balancing.")],
    "08230102": [("Web Development", "Tech & Coding", "Expert", 96, "Responsive sites and web apps."),
                 ("React", "Tech & Coding", "Advanced", 90, "Component-based interfaces."),
                 ("NodeJS", "Tech & Coding", "Advanced", 86, "REST APIs and tooling.")],
    "08230103": [("Tutoring", "Academics & Tutoring", "Expert", 95, "One-to-one and small-group tutoring."),
                 ("Mathematics", "Academics & Tutoring", "Expert", 94, "Algebra, statistics and proofs."),
                 ("Calculus", "Academics & Tutoring", "Advanced", 90, "Limits, derivatives and integrals.")],
    "08230104": [("Drawing", "Design & Arts", "Expert", 95, "Sketching and character illustration."),
                 ("Illustrator", "Design & Arts", "Advanced", 90, "Vector graphics."),
                 ("Logo Art", "Design & Arts", "Advanced", 88, "Minimal logo design.")],
    "08230105": [("Music", "Music", "Expert", 96, "Performance and arrangement."),
                 ("Piano Instructor", "Music", "Advanced", 92, "Beginner to intermediate lessons."),
                 ("Music Theory", "Music", "Advanced", 88, "Scales, harmony and notation.")],
    "08230106": [("Writing", "Writing & Languages", "Advanced", 90, "Essays, articles and stories."),
                 ("Copywriting", "Writing & Languages", "Advanced", 86, "Short punchy copy."),
                 ("Proofreading", "Writing & Languages", "Expert", 94, "Grammar and style checks.")],
    "08230107": [("SQL Database Design", "Tech & Coding", "Advanced", 88, "Normalisation and schema design."),
                 ("Excel", "Tech & Coding", "Intermediate", 70, "Formulas and pivot tables."),
                 ("Query Tuning", "Tech & Coding", "Intermediate", 65, "Indexes and execution plans.")],
    "08230108": [("React", "Tech & Coding", "Intermediate", 62, "Hooks and state management.")],
    "08230109": [("Photography", "Design & Arts", "Advanced", 88, "Portrait sessions.")],
    "08230110": [("Figma Prototyping", "Design & Arts", "Advanced", 90, "Interactive prototypes."),
                 ("UI/UX Design", "Design & Arts", "Advanced", 86, "Wireframes and flows.")],
    "08230111": [("Photography", "Design & Arts", "Advanced", 90, "Portraits and travel."),
                 ("Photo Editing", "Media Production", "Intermediate", 72, "Colour and crop edits.")],
    "08230112": [("React Development", "Tech & Coding", "Intermediate", 68, "Hooks and components.")],
    "08230113": [("Backend Server Setup", "Tech & Coding", "Advanced", 85, "Linux servers and deployment."),
                 ("NodeJS", "Tech & Coding", "Intermediate", 70, "APIs and middleware.")],
    "08230114": [("Creative Copywriting", "Writing & Languages", "Advanced", 84, "Posters and captions.")],
    "08230115": [("Excel", "Tech & Coding", "Intermediate", 66, "Data cleaning and charts.")],
    "08230116": [("Video Editing", "Media Production", "Intermediate", 64, "Event highlight reels.")],
}

_ACHIEVEMENT_SEED = {
    "08230188": [
        "Tech State Hackathon 2025 - Best UI/UX Design Winner",
        "Design Lead at Campus Computer Society",
        "Completed 15 campus tutoring exchanges in Typography",
    ],
    "08230101": ["Best Photographer - Annual College Fest 2025"],
    "08230102": ["Winner - Inter-college Hackathon 2025"],
    "08230103": ["Peer Tutor of the Year 2025"],
}

# (student_id, title, tag, days_ago, thumbnail colour, description)
_PORTFOLIO_SEED = [
    ("08230188", "Campus Event Poster", "Graphic Design", 2, "#7DC3EA", "Poster for the Academic Feest event."),
    ("08230188", "Mobile App UI Design", "UI/UX Design", 7, "#D6DAE0", "Mobile app interface for a study planner."),
    ("08230188", "Photography Collection", "Photography", 14, "#C9742B", "Autumn campus photography series."),
    ("08230188", "Video Reel Highlight", "Videography", 21, "#3B3A2E", "Highlight reel of a short film shoot."),
    ("08230188", "Website Redesign", "Web Development", 30, "#8A93A6", "Redesign concept for a club website."),
    ("08230188", "Digital Illustration", "Digital Art", 30, "#EFE6D2", "Digital portrait illustration."),
    ("08230101", "Portrait Series", "Photography", 6, "#B08968", "Natural-light portrait set."),
    ("08230102", "Club Registration Site", "Web Development", 12, "#64748B", "React site for club sign-ups."),
    ("08230116", "Website Crack Activation Hacks", "Video Editing", 1, "#475569", "Tutorial video."),
    ("08230104", "Fest Logo Pack", "Logo Art", 3, "#F59E0B", "Logo variations for the college fest."),
    ("08230114", "Spam Flyer Pack", "Creative Copywriting", 1, "#A78BFA", "Mass-produced flyer text."),
]

# (from, to, skill, message, status, days_ago)  - 'to' is the provider
_REQUEST_SEED = [
    ("08230108", "08230188", "React App Debugging", "Hey! I am running into state circular loops in my project. I need an hour of hands-on pairing help.", STATUS_PENDING, 0),
    ("08230109", "08230188", "Photography Session", "Need some high-quality portrait shots taken on campus for my grad portfolio. Can offer graphic design help in return!", STATUS_ACCEPTED, 1),
    ("08230107", "08230188", "SQL Database Design", "Helping a student club with database setup. Need advice on normal form and schema structure.", STATUS_DECLINED, 2),
    ("08230110", "08230188", "Figma Prototyping", "Need to make interactive prototype for my startup project presentation. Will take under 2 hours.", STATUS_COMPLETED, 7),
    ("08230188", "08230113", "Backend Server Setup", "Could you help me set up a small Node server for my class project?", STATUS_ACCEPTED, 3),
    ("08230188", "08230114", "Creative Copywriting", "I need catchy copy for our club recruitment poster.", STATUS_PENDING, 1),
    ("08230188", "08230105", "Music Theory", "Would love a quick lesson on chord progressions for my video project.", STATUS_COMPLETED, 14),
    ("08230102", "08230103", "Calculus", "Could you help me revise integration techniques before the exam?", STATUS_PENDING, 2),
    ("08230106", "08230101", "Portrait Editing", "Please teach me basic Lightroom portrait retouching.", STATUS_ACCEPTED, 4),
]

# (request_id, from, to, skill, rating, comment, days_ago)
_FEEDBACK_SEED = [
    (0, "08230111", "08230188", "Photography", 5, "Alex took absolutely stunning campus portraits for my graduation portfolio! Extremely professional and fast.", 2),
    (0, "08230101", "08230188", "Graphic Design", 5, "Incredibly fast turnaround on our student club flyer. Got so many compliments on the creative layout.", 7),
    (0, "08230112", "08230188", "React Development", 4, "Helped resolve our state loops efficiently. Very friendly peer tutor.", 14),
]

# (target_type, target_title, reason, reporter, hours_ago)
_REPORT_SEED = [
    ("Portfolio", "Website Crack Activation Hacks", "Violation of campus software policies", "08230102", 3),
    ("Portfolio", "Spam Flyer Pack", "Spam / irrelevant content", "08230103", 9),
    ("Student", "Profile: Kuenga", "Inappropriate content in profile", "08230105", 26),
]


class DataStore:
    """Holds every table and exposes the queries/updates the screens need."""

    def __init__(self):
        self._build_tables()

    # ------------------------------------------------------------------
    # Table construction
    # ------------------------------------------------------------------
    def _build_tables(self) -> None:
        students = [
            {
                "student_id": sid, "full_name": name, "email": _email_for(sid),
                "course": course, "year_label": "Class of 2026", "bio": bio,
                "experience": exp, "recent_activity": recent, "rating": rating,
                "review_count": reviews, "collab_count": collabs,
                "password": "Dorji@123456" if sid == "08230188" else DEFAULT_STUDENT_PASSWORD,
                "status": "Active", "role": ROLE_STUDENT, "photo_path": "",
            }
            for sid, name, course, rating, reviews, collabs, bio, exp, recent in _STUDENT_SEED
        ]
        students.append({
            "student_id": "ADMIN01", "full_name": "Super Admin",
            "email": f"admin@{EMAIL_DOMAIN}", "course": "Security & Content",
            "year_label": "Security & Content", "bio": "", "experience": "",
            "recent_activity": "", "rating": 0.0, "review_count": 0, "collab_count": 0,
            "password": "Admin@12345", "status": "Active", "role": ROLE_ADMIN, "photo_path": "",
        })
        self.students = pd.DataFrame(students, columns=STUDENT_COLUMNS)

        skill_rows, skill_id = [], 1
        for sid, items in _SKILL_SEED.items():
            for name, category, level, pct, desc in items:
                skill_rows.append([skill_id, sid, name, category, level, pct, desc])
                skill_id += 1
        self.skills = pd.DataFrame(skill_rows, columns=SKILL_COLUMNS)

        ach_rows, ach_id = [], 1
        for sid, items in _ACHIEVEMENT_SEED.items():
            for text in items:
                ach_rows.append([ach_id, sid, text])
                ach_id += 1
        self.achievements = pd.DataFrame(ach_rows, columns=ACHIEVEMENT_COLUMNS)

        self.portfolio = pd.DataFrame(
            [[i + 1, sid, title, tag, days, color, desc, ""]
             for i, (sid, title, tag, days, color, desc) in enumerate(_PORTFOLIO_SEED)],
            columns=PORTFOLIO_COLUMNS,
        )
        self.requests = pd.DataFrame(
            [[i + 1, *row] for i, row in enumerate(_REQUEST_SEED)], columns=REQUEST_COLUMNS
        )
        self.feedback = pd.DataFrame(
            [[i + 1, *row] for i, row in enumerate(_FEEDBACK_SEED)], columns=FEEDBACK_COLUMNS
        )

        report_rows = []
        for i, (ttype, title, reason, reporter, hours) in enumerate(_REPORT_SEED):
            target_id = self._find_report_target(ttype, title)
            report_rows.append([i + 1, ttype, target_id, title, reason, reporter, hours, "Open"])
        self.reports = pd.DataFrame(report_rows, columns=REPORT_COLUMNS)

    def _find_report_target(self, target_type: str, title: str) -> str:
        """Resolve the seeded report title to the id of the reported record."""
        if target_type == "Portfolio":
            match = self.portfolio[self.portfolio["title"] == title]
            return str(match.iloc[0]["item_id"]) if not match.empty else ""
        name = title.replace("Profile: ", "")
        match = self.students[self.students["full_name"] == name]
        return str(match.iloc[0]["student_id"]) if not match.empty else ""

    @staticmethod
    def _next_id(frame: pd.DataFrame, column: str) -> int:
        return int(frame[column].max()) + 1 if not frame.empty else 1

    @staticmethod
    def _append(frame: pd.DataFrame, row: dict) -> pd.DataFrame:
        return pd.concat([frame, pd.DataFrame([row])], ignore_index=True)

    # ------------------------------------------------------------------
    # Authentication & accounts
    # ------------------------------------------------------------------
    def authenticate(self, identifier: str, password: str, as_admin: bool = False):
        """Return ``(user_dict, "")`` on success or ``(None, error_message)``."""
        identifier = identifier.strip().lower()
        df = self.students
        match = df[
            (df["email"].str.lower() == identifier)
            | (df["student_id"].str.lower() == identifier)
        ]
        if match.empty:
            return None, "No account found with those details."
        user = match.iloc[0].to_dict()
        if user["password"] != password:
            return None, "Incorrect password. Please try again."
        if as_admin and user["role"] != ROLE_ADMIN:
            return None, "This account does not have administrator access."
        if not as_admin and user["role"] == ROLE_ADMIN:
            return None, "Administrators must use 'Sign In as Admin'."
        if user["status"] == "Suspended":
            return None, "This account is suspended. Please contact the administrator."
        return user, ""

    def register_student(self, form: dict) -> None:
        """Create a student account. Raises ``ValueError`` for duplicates."""
        email = form["email"].strip().lower()
        sid = form["student_id"].strip()
        if (self.students["student_id"] == sid).any():
            raise ValueError("An account with this Student ID already exists.")
        if (self.students["email"].str.lower() == email).any():
            raise ValueError("An account with this campus email already exists.")
        row = {
            "student_id": sid, "full_name": form["full_name"].strip(), "email": email,
            "course": form["course"].strip(), "year_label": "Class of 2026", "bio": "",
            "experience": "", "recent_activity": "", "rating": 0.0, "review_count": 0,
            "collab_count": 0, "password": form["password"], "status": "Active",
            "role": ROLE_STUDENT, "photo_path": "",
        }
        self.students = self._append(self.students, row)

    def reset_password(self, email: str) -> bool:
        """Demo password reset: returns True if the email belongs to an account."""
        return (self.students["email"].str.lower() == email.strip().lower()).any()

    # ------------------------------------------------------------------
    # Students & profile
    # ------------------------------------------------------------------
    def get_student(self, student_id: str) -> dict:
        match = self.students[self.students["student_id"] == student_id]
        return match.iloc[0].to_dict() if not match.empty else {}

    def update_profile(self, student_id: str, **fields) -> None:
        """Update profile columns. Raises ``ValueError`` if the email is taken."""
        email = fields.get("email")
        if email:
            taken = self.students[
                (self.students["email"].str.lower() == email.lower())
                & (self.students["student_id"] != student_id)
            ]
            if not taken.empty:
                raise ValueError("That campus email is already used by another account.")
        for column, value in fields.items():
            self.students.loc[self.students["student_id"] == student_id, column] = value

    def get_achievements(self, student_id: str) -> list:
        rows = self.achievements[self.achievements["student_id"] == student_id]
        return rows[["achievement_id", "text"]].to_dict("records")

    def replace_achievements(self, student_id: str, texts: list) -> None:
        self.achievements = self.achievements[self.achievements["student_id"] != student_id]
        for text in texts:
            row = {
                "achievement_id": self._next_id(self.achievements, "achievement_id"),
                "student_id": student_id, "text": text,
            }
            self.achievements = self._append(self.achievements, row)

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------
    def get_skills(self, student_id: str) -> list:
        rows = self.skills[self.skills["student_id"] == student_id]
        return rows.sort_values("proficiency", ascending=False).to_dict("records")

    def top_skills(self, student_id: str, limit: int = 3) -> list:
        return [s["name"] for s in self.get_skills(student_id)[:limit]]

    def add_skill(self, student_id: str, name: str, category: str, level: str, description: str) -> None:
        row = {
            "skill_id": self._next_id(self.skills, "skill_id"), "student_id": student_id,
            "name": name.strip(), "category": category, "level": level,
            "proficiency": LEVEL_TO_PERCENT.get(level, 50), "description": description.strip(),
        }
        self.skills = self._append(self.skills, row)

    def delete_skill(self, skill_id: int) -> None:
        self.skills = self.skills[self.skills["skill_id"] != skill_id]

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search_students(self, query: str = "", category: str = ALL_CATEGORIES,
                        exclude_id: str = "", limit: int = 6) -> list:
        """Search active students by name, skill or category."""
        query = query.strip().lower()
        pool = self.students[
            (self.students["role"] == ROLE_STUDENT)
            & (self.students["status"] == "Active")
            & (self.students["student_id"] != exclude_id)
        ]
        results = []
        for _, student in pool.iterrows():
            skills = self.skills[self.skills["student_id"] == student["student_id"]]
            if skills.empty:
                continue
            if category and category != ALL_CATEGORIES and not (skills["category"] == category).any():
                continue
            if query:
                haystack = [student["full_name"].lower()]
                haystack += skills["name"].str.lower().tolist()
                haystack += skills["category"].str.lower().tolist()
                if not any(query in text for text in haystack):
                    continue
            record = student.to_dict()
            record["top_skills"] = self.top_skills(student["student_id"])
            results.append(record)
        results.sort(key=lambda r: (-r["rating"], r["full_name"]))
        return results[:limit]

    # ------------------------------------------------------------------
    # Portfolio
    # ------------------------------------------------------------------
    def get_portfolio(self, student_id: str) -> list:
        rows = self.portfolio[self.portfolio["student_id"] == student_id]
        return rows.sort_values("days_ago").to_dict("records")

    def add_portfolio_item(self, student_id: str, title: str, tag: str,
                           description: str, image_path: str = "") -> None:
        row = {
            "item_id": self._next_id(self.portfolio, "item_id"), "student_id": student_id,
            "title": title.strip(), "skill_tag": tag, "days_ago": 0, "color": "#BFDBFE",
            "description": description.strip(), "image_path": image_path,
        }
        self.portfolio = self._append(self.portfolio, row)

    def update_portfolio_item(self, item_id: int, **fields) -> None:
        for column, value in fields.items():
            self.portfolio.loc[self.portfolio["item_id"] == item_id, column] = value

    def delete_portfolio_item(self, item_id: int) -> None:
        self.portfolio = self.portfolio[self.portfolio["item_id"] != item_id]

    # ------------------------------------------------------------------
    # Skill requests
    # ------------------------------------------------------------------
    def _decorate_requests(self, rows: pd.DataFrame, other_column: str) -> list:
        records = []
        for record in rows.sort_values("days_ago").to_dict("records"):
            other = self.get_student(record[other_column])
            record["other_id"] = record[other_column]
            record["other_name"] = other.get("full_name", "Unknown")
            records.append(record)
        return records

    def incoming_requests(self, student_id: str) -> list:
        return self._decorate_requests(self.requests[self.requests["to_id"] == student_id], "from_id")

    def sent_requests(self, student_id: str) -> list:
        return self._decorate_requests(self.requests[self.requests["from_id"] == student_id], "to_id")

    def create_request(self, from_id: str, to_id: str, skill: str, message: str) -> None:
        row = {
            "request_id": self._next_id(self.requests, "request_id"), "from_id": from_id,
            "to_id": to_id, "skill": skill, "message": message.strip(),
            "status": STATUS_PENDING, "days_ago": 0,
        }
        self.requests = self._append(self.requests, row)

    def has_pending_request(self, from_id: str, to_id: str, skill: str) -> bool:
        """True if an identical request is already waiting for an answer."""
        rows = self.requests[
            (self.requests["from_id"] == from_id) & (self.requests["to_id"] == to_id)
            & (self.requests["skill"] == skill) & (self.requests["status"] == STATUS_PENDING)
        ]
        return not rows.empty

    def update_request_status(self, request_id: int, status: str) -> None:
        mask = self.requests["request_id"] == request_id
        self.requests.loc[mask, "status"] = status
        if status == STATUS_COMPLETED:
            for column in ("from_id", "to_id"):
                sid = self.requests.loc[mask, column].iloc[0]
                self.students.loc[self.students["student_id"] == sid, "collab_count"] += 1

    def count_pending_incoming(self, student_id: str) -> int:
        rows = self.requests[(self.requests["to_id"] == student_id) & (self.requests["status"] == STATUS_PENDING)]
        return len(rows)

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------
    def feedback_received(self, student_id: str) -> list:
        rows = self.feedback[self.feedback["to_id"] == student_id].sort_values("days_ago")
        records = []
        for record in rows.to_dict("records"):
            record["from_name"] = self.get_student(record["from_id"]).get("full_name", "Unknown")
            records.append(record)
        return records

    def reviewable_collaborations(self, student_id: str) -> list:
        """Completed collaborations the student has not yet reviewed."""
        done = self.requests[
            (self.requests["status"] == STATUS_COMPLETED)
            & ((self.requests["from_id"] == student_id) | (self.requests["to_id"] == student_id))
        ]
        reviewed = set(self.feedback[self.feedback["from_id"] == student_id]["request_id"])
        items = []
        for record in done.to_dict("records"):
            if record["request_id"] in reviewed:
                continue
            other_id = record["to_id"] if record["from_id"] == student_id else record["from_id"]
            other_name = self.get_student(other_id).get("full_name", "Unknown")
            items.append({
                "request_id": record["request_id"], "other_id": other_id,
                "skill": record["skill"], "label": f"{other_name} - {record['skill']}",
            })
        return items

    def add_feedback(self, request_id: int, from_id: str, to_id: str,
                     skill: str, rating: int, comment: str) -> None:
        row = {
            "feedback_id": self._next_id(self.feedback, "feedback_id"), "request_id": request_id,
            "from_id": from_id, "to_id": to_id, "skill": skill, "rating": rating,
            "comment": comment.strip(), "days_ago": 0,
        }
        self.feedback = self._append(self.feedback, row)
        target = self.students["student_id"] == to_id
        count = int(self.students.loc[target, "review_count"].iloc[0])
        current = float(self.students.loc[target, "rating"].iloc[0])
        self.students.loc[target, "rating"] = round((current * count + rating) / (count + 1), 1)
        self.students.loc[target, "review_count"] = count + 1

    # ------------------------------------------------------------------
    # Reports & administration
    # ------------------------------------------------------------------
    def create_report(self, target_type: str, target_id: str, title: str,
                      reason: str, reporter_id: str) -> None:
        row = {
            "report_id": self._next_id(self.reports, "report_id"), "target_type": target_type,
            "target_id": str(target_id), "title": title, "reason": reason,
            "reporter_id": reporter_id, "hours_ago": 0, "status": "Open",
        }
        self.reports = self._append(self.reports, row)

    def open_reports(self) -> list:
        rows = self.reports[self.reports["status"] == "Open"].sort_values("hours_ago")
        return rows.to_dict("records")

    def resolve_report(self, report_id: int, take_down: bool) -> None:
        """Dismiss a report, or take down the reported content."""
        mask = self.reports["report_id"] == report_id
        report = self.reports[mask].iloc[0]
        if take_down:
            if report["target_type"] == "Portfolio" and report["target_id"]:
                self.delete_portfolio_item(int(report["target_id"]))
            elif report["target_type"] == "Student" and report["target_id"]:
                self.set_student_status(report["target_id"], "Suspended")
            self.reports.loc[mask, "status"] = "Actioned"
        else:
            self.reports.loc[mask, "status"] = "Dismissed"

    def directory(self, filter_text: str = "") -> pd.DataFrame:
        """Student directory for the admin panel (with a registered-skills count)."""
        df = self.students[self.students["role"] == ROLE_STUDENT].copy()
        counts = self.skills.groupby("student_id").size()
        df["skills_count"] = df["student_id"].map(counts).fillna(0).astype(int)
        filter_text = filter_text.strip().lower()
        if filter_text:
            mask = (
                df["full_name"].str.lower().str.contains(filter_text, regex=False)
                | df["student_id"].str.contains(filter_text, regex=False)
            )
            df = df[mask]
        return df[["full_name", "student_id", "email", "skills_count", "status"]].reset_index(drop=True)

    def set_student_status(self, student_id: str, status: str) -> None:
        self.students.loc[self.students["student_id"] == student_id, "status"] = status
