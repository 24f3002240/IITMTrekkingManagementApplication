# Trekking Management System

A web app built with Flask that handles trekking bookings end-to-end — from an admin creating treks and assigning staff, to users browsing and booking them. Three separate role-based portals keep things clean: Admin, Staff, and User.

Built this as a project to practice Flask blueprints, SQLAlchemy relationships, and session-based auth with Flask-Login.

---

## What it does

**Admin** can create and manage treks, approve staff registrations, assign staff members to treks, blacklist accounts, and see everything happening on the platform.

**Staff** get their own view showing only the treks assigned to them. They can update the trek status (open it for bookings, close it, mark it complete) and see who's booked.

**Users** register, browse open treks, filter by difficulty or location, book a spot, or cancel if plans change.

A few things I made sure to handle properly:
- Duplicate trek detection (same name + location + overlapping dates)
- Staff schedule conflict check when assigning to a trek
- Users can't double-book, and can't book two treks with overlapping dates
- Slots auto-update on booking and cancellation
- Staff accounts sit in a `pending` state until the admin approves them

---

## Stack

- **Flask** — routing, blueprints, request handling
- **Flask-SQLAlchemy** — ORM on top of SQLite
- **Flask-Login** — session management and `current_user`
- **Werkzeug** — password hashing
- **Jinja2** — templating (comes with Flask)
- **SQLite** — database, stored in `instance/trekking.db`

---

## Project layout

```
TrekkingManagement/
├── app.py               # create_app() factory, login_manager setup
├── config.py            # secret key, DB path, seeded admin credentials
├── database.py          # db init + admin seed on first run
├── models.py            # User, Trek, Booking models
├── requirements.txt
│
├── routes/
│   ├── auth.py          # register, login, logout
│   ├── admin.py         # everything the admin does
│   ├── staff.py         # staff dashboard, status updates, participants
│   └── user.py          # browse treks, book, cancel, profile
│
├── templates/
│   ├── base.html
│   ├── auth/
│   ├── admin/
│   ├── staff/
│   └── user/
│
├── static/
│   └── css/style.css
│
└── utils/
    └── decorators.py    # role_required() decorator
```

---

## Data models

### User

```
id, name, email, password_hash
role            → 'admin' | 'staff' | 'user'
approval_status → 'pending' | 'approved'   (matters for staff)
is_blacklisted  → bool
created_at
```

### Trek

```
id, name, location
difficulty     → 'Easy' | 'Moderate' | 'Hard'
duration_days
available_slots
status         → Pending → Approved → Open → Closed / Completed
start_date, end_date
assigned_staff_id  (FK → users.id)
```

### Booking

```
id
user_id   (FK → users.id)
trek_id   (FK → treks.id)
booking_date
status    → 'Booked' | 'Cancelled' | 'Completed'
```

---

## Who can do what

|                                   | Admin | Staff | User |
|-----------------------------------|-------|-------|------|
| Create / edit / delete treks      | yes   | no    | no   |
| Approve treks                     | yes   | no    | no   |
| Assign staff to a trek            | yes   | no    | no   |
| Approve staff accounts            | yes   | no    | no   |
| Blacklist accounts                | yes   | no    | no   |
| See all bookings                  | yes   | no    | no   |
| Update trek status and slots      | no    | yes   | no   |
| View participants for a trek      | no    | yes   | no   |
| Browse and book open treks        | no    | no    | yes  |
| Cancel their own booking          | no    | no    | yes  |
| Edit their profile                | no    | no    | yes  |

Admin cannot be blacklisted. Staff login is blocked until the admin approves their account.

---

## Setup

**1. Clone and navigate into the project**

```bash
git clone <repo-url>
cd TrekkingManagement
```

**2. Create a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure before running**

Open `config.py` and change the secret key and admin credentials:

```python
SECRET_KEY = 'something-hard-to-guess'
ADMIN_EMAIL = 'your@email.com'
ADMIN_PASSWORD = 'your-password'
```

Do not commit real credentials. For any deployment, pull these from environment variables instead.

**5. Run**

```bash
python app.py
```

App runs at `http://127.0.0.1:5000`. The database is created automatically on first startup, and the admin account gets seeded from whatever is in `config.py`.

---

## Routes reference

| Blueprint | Prefix   | Notable routes                                                   |
|-----------|----------|------------------------------------------------------------------|
| auth      | /auth    | `/login`, `/register`, `/logout`                                 |
| admin     | /admin   | `/dashboard`, `/treks`, `/treks/create`, `/trek/<id>/approve`    |
| staff     | /staff   | `/dashboard`, `/trek/<id>/update`, `/trek/<id>/participants`     |
| user      | /user    | `/dashboard`, `/treks`, `/trek/<id>/book`, `/booking/<id>/cancel`|

---

## Notes

- The trek lifecycle is strictly enforced: a trek must be assigned a staff member before it can be approved, and status transitions follow a fixed path (Pending → Approved → Open → Closed/Completed).
- Cancelling a booking returns the slot to the trek automatically.
- Staff registration goes through a pending state — they can register but can't log in until approved.
