# StudentSkill Hub (Tkinter)

A desktop app where university students showcase skills and talents, and request help from peers.
An administrator can manage accounts, moderate reported content and view analytics.
Built from the Figma prototype "GUI Project". All data is static and held in pandas DataFrames.

## Run
```
pip install -r requirements.txt     # tkinter ships with Python (on Linux: sudo apt install python3-tk)
python main.py
```

## Demo accounts
| Role    | Username / email          | Password       |
|---------|---------------------------|----------------|
| Student | 08230188.sce@rub.edu.bt   | Dorji@123456   |
| Student | any other seeded student  | Student@123    |
| Admin   | admin@rub.edu.bt          | Admin@12345    |

Use **Sign In as Admin** on the login card for the admin account. You can also register a new student.

## Project structure
```
main.py            Tkinter desktop-app entry point
app.py             App window: session, navigation, sidebar/topbar wiring
config.py          design tokens (colours, fonts, icons) and constants
data/store.py      static "database": pandas DataFrames + all queries/updates
data/analytics.py  numpy-generated campus analytics (pandas DataFrames)
utils/validators.py  all input validation (returns (ok, message))
utils/charts.py    matplotlib figure builders (no Tkinter code)
utils/helpers.py   small formatting helpers
widgets/components.py  reusable widgets (buttons, cards, form fields, tabs, scrolling)
widgets/dialogs.py     modal dialogs
widgets/shell.py       sidebar + top bar
screens/           one module per page: auth, dashboard, profile, skills, search,
                   portfolio, requests, feedback, admin
```

## Tables (for the ERD)
students(PK student_id) | skills(PK skill_id, FK student_id) | achievements(PK, FK student_id)
portfolio(PK item_id, FK student_id) | requests(PK request_id, FK from_id, FK to_id)
feedback(PK feedback_id, FK request_id, from_id, to_id) | reports(PK report_id, target_type + target_id)

## Notes
- Data is in memory only: changes last until the program closes.
- Student ID is read-only on the profile page (it is the primary key).
- The admin sidebar shows only "Admin Panel"; analytics is the second tab inside that page.
