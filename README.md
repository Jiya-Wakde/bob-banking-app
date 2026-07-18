# Banking Workshop — SecureBank

A simple, fully-featured banking web application built with **Python Flask**, **SQLite**, and **Bootstrap 5**.

## Features

| Feature | Details |
|---|---|
| Login / Logout | Secure password hashing (Werkzeug), server-side session |
| Dashboard | View current account balance |
| Deposit | Add funds with server-side validation |
| Withdrawal | Deduct funds; overdraft protection |
| Session guard | All pages except login redirect unauthenticated users |

---

## Project Structure

```
banking-workshop/
├── FRONTEND/
│   ├── templates/
│   │   ├── login.html          ← login page
│   │   └── dashboard.html      ← balance + transaction page
│   └── static/
│       └── styles.css          ← Bootstrap overrides
│
└── BACKEND/
    ├── app.py                  ← Flask app, routes
    ├── auth.py                 ← login/logout/session guard
    ├── account.py              ← deposit/withdraw business logic
    ├── database/
    │   ├── db.py               ← SQLite connection helper
    │   ├── seed.py             ← creates schema + test users
    │   └── bank.db             ← (auto-created by seed.py)
    ├── tests/
    │   ├── test_account.py     ← unit tests
    │   └── test_routes.py      ← integration tests
    └── requirements.txt
```

---

## Quick Start

### 1. Prerequisites

- Python 3.9+
- pip

### 2. Create and activate a virtual environment

```powershell
cd BACKEND
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Seed the database (run once)

```powershell
python database/seed.py
```

### 5. Start the server

```powershell
flask run
```

Open your browser at **http://127.0.0.1:5000**

### 6. Demo accounts

| Username | Password | Starting Balance |
|---|---|---|
| `alice` | `password123` | $2,500.00 |
| `bob` | `securepass` | $750.50 |

---

## Running Tests

```powershell
cd BACKEND
pytest tests/ -v
```

---

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Signs Flask session cookies | `dev-secret-change-in-production` |
| `FLASK_DEBUG` | Enable debug/reload mode | not set (off) |

Set these before running in any environment:

```powershell
$env:SECRET_KEY = "your-long-random-secret"
flask run
```

---

## Security Notes

- Passwords are **never stored in plain text** — only Werkzeug `pbkdf2:sha256` hashes.
- All SQL queries use **parameterised statements** — no SQL injection risk.
- The database schema enforces `balance >= 0` at the DB level as a last-resort guard.
- `session.clear()` on logout immediately invalidates the server-side session.
