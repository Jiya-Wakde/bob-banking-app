# Banking Web Application — Implementation Plan

> **Status:** Planning  
> **Stack:** HTML + Bootstrap (Frontend) · Python Flask (Backend) · SQLite (Database)

---

## 1. Solution Overview

### Objective

Build a browser-based banking application that allows registered customers to securely
log in, view their account balance, deposit funds, withdraw funds, and log out — all
through a clean, responsive web interface backed by a lightweight Python API.

### Scope

| In Scope | Out of Scope |
|---|---|
| Customer login / logout | User registration / sign-up flow |
| View current account balance | Multi-account support |
| Deposit funds | Transfers between accounts |
| Withdraw funds | Admin / bank-staff portal |
| Session management | External payment integrations |
| Basic input validation (client + server) | Email / SMS notifications |

### Users

| User Type | Description |
|---|---|
| **Customer** | A pre-seeded bank account holder who logs in to manage their own account |

### Functional Requirements

1. A customer can authenticate with a username and password.
2. An authenticated customer can view their current account balance on a dashboard.
3. An authenticated customer can deposit a positive monetary amount.
4. An authenticated customer can withdraw a positive monetary amount not exceeding their current balance.
5. An authenticated customer can log out, terminating their session.
6. All protected pages redirect unauthenticated users to the login page.

### Non-Functional Requirements

| Concern | Expectation |
|---|---|
| **Security** | Passwords stored as hashed values; session tokens managed server-side via Flask sessions |
| **Usability** | Responsive layout via Bootstrap; works on desktop and mobile browsers |
| **Simplicity** | No build pipeline required; runnable with a single `flask run` command |
| **Portability** | SQLite database file stored inside the backend folder; no external DB server needed |
| **Maintainability** | Clear separation of frontend and backend concerns via dedicated folders |

### Assumptions

- Customer accounts are pre-seeded in the database (no self-registration flow).
- A single currency is used; no formatting for multiple locales is required.
- The application runs on localhost during development; no production deployment is planned.
- Flask's built-in development server is sufficient for this workshop context.
- Bootstrap is loaded via CDN; no local asset bundling is needed.

---

## 2. High-Level Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER                                 │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                  FRONTEND  (FRONTEND/)                   │  │
│   │                                                          │  │
│   │   HTML Pages          Bootstrap CSS       JavaScript     │  │
│   │   login.html          (CDN)               form submit    │  │
│   │   dashboard.html                          fetch / XHR    │  │
│   └──────────────────────┬───────────────────────────────────┘  │
└─────────────────────────-│───────────────────────────────────────┘
                           │  HTTP Requests (form POST / AJAX)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND  (BACKEND/)                        │
│                                                                 │
│   ┌──────────────┐   ┌──────────────┐   ┌───────────────────┐  │
│   │  Flask App   │   │  Route Layer │   │  Business Logic   │  │
│   │  app.py      │──▶│  /login      │──▶│  auth service     │  │
│   │              │   │  /dashboard  │   │  account service  │  │
│   │              │   │  /deposit    │   │  transaction svc  │  │
│   │              │   │  /withdraw   │   │                   │  │
│   │              │   │  /logout     │   │                   │  │
│   └──────────────┘   └──────────────┘   └────────┬──────────┘  │
│                                                   │             │
└───────────────────────────────────────────────────│─────────────┘
                                                    │  SQL queries
                                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATABASE  (BACKEND/database/)                 │
│                                                                 │
│                        SQLite  bank.db                          │
│              [ customers ]    [ transactions ]                  │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

```
Frontend (HTML form)
     │
     │  POST /login  {username, password}
     ▼
Backend (Flask route)
     │  validate credentials via auth service
     │
     ├─► Database: SELECT customer WHERE username = ?
     │       └─ compare hashed password
     │
     ├─ on success → create server-side session → redirect /dashboard
     └─ on failure → re-render login with error message
```

### Request Lifecycle

```
1. Browser sends HTTP request to Flask route
2. Flask session middleware checks authentication state
3. Route handler delegates to the appropriate service function
4. Service function queries / updates the SQLite database
5. Flask renders an HTML template (or returns JSON) and sends response
6. Browser re-renders the page / updates the UI
```

---

## 3. Component Design

### Frontend Responsibilities (`FRONTEND/`)

| Concern | Detail |
|---|---|
| **Presentation** | Render HTML pages styled with Bootstrap for a clean, responsive layout |
| **Forms** | Collect user credentials, deposit amount, and withdrawal amount |
| **Validation** | Basic client-side checks (non-empty fields, positive numbers) before submission |
| **Navigation** | Provide links between Login → Dashboard → Logout |
| **Feedback** | Display server-returned success/error messages to the user |
| **No business logic** | All balance calculations and auth decisions happen on the backend |

### Backend Responsibilities (`BACKEND/`)

| Concern | Detail |
|---|---|
| **Routing** | Map HTTP endpoints to handler functions |
| **Authentication** | Verify credentials, create/destroy sessions, guard protected routes |
| **Business Logic** | Enforce deposit/withdrawal rules (positive amounts, sufficient balance) |
| **Data Access** | Abstract all database queries behind service/helper functions |
| **Response** | Render templates or return JSON payloads to the frontend |
| **Session Management** | Track logged-in state across requests using Flask session |

### Database Responsibilities (`BACKEND/database/`)

| Concern | Detail |
|---|---|
| **Persistence** | Store customer account data and transaction history in SQLite |
| **Integrity** | Enforce constraints so balance never goes negative at the data layer |
| **Seeding** | Provide initial customer records for testing without a registration UI |
| **Isolation** | All DB interaction is encapsulated; frontend never touches the database directly |

---

## 4. Folder Structure

```
banking-workshop/
│
├── IMPLEMENTATION_PLAN.md          ← this document
│
├── FRONTEND/                       ← all browser-facing assets
│   ├── templates/                  ← HTML page templates
│   │   ├── login.html              ← login form page
│   │   └── dashboard.html          ← balance + transaction actions page
│   └── static/                     ← optional local CSS / JS overrides
│       └── styles.css
│
└── BACKEND/                        ← all server-side code
    ├── app.py                      ← Flask application entry point; route definitions
    ├── auth.py                     ← authentication helpers (login, logout, session guard)
    ├── account.py                  ← account service (read balance, deposit, withdraw)
    ├── database/
    │   ├── db.py                   ← database connection helper and query utilities
    │   ├── seed.py                 ← script to pre-populate customer records
    │   └── bank.db                 ← SQLite database file (auto-created at runtime)
    └── requirements.txt            ← Python dependencies (Flask, etc.)
```

### Responsibility of Each Folder

| Folder / File | Responsibility |
|---|---|
| `FRONTEND/templates/` | HTML templates served by Flask (Jinja2); defines all UI pages |
| `FRONTEND/static/` | Optional local CSS/JS; Bootstrap loaded from CDN |
| `BACKEND/app.py` | Application factory, route registration, session configuration |
| `BACKEND/auth.py` | Login credential checking, session creation/destruction, route protection decorator |
| `BACKEND/account.py` | Business rules for balance enquiry, deposit, and withdrawal operations |
| `BACKEND/database/db.py` | SQLite connection management, parameterised query helper |
| `BACKEND/database/seed.py` | One-time script to insert test customer accounts |
| `BACKEND/database/bank.db` | SQLite file; created by the seed script or app on first run |
| `BACKEND/requirements.txt` | Pinned list of Python packages required to run the backend |

---

## 5. Module Breakdown

### 5.1 Authentication Module

**Purpose:** Control who can access the application and for how long.

| Concern | Behaviour |
|---|---|
| Login | Accept username + password; validate against hashed value in DB; create session on success |
| Session Guard | Decorator / before-request hook that redirects unauthenticated requests to `/login` |
| Logout | Clear session data and redirect to login page |
| Password Storage | Passwords persisted as hashed strings (e.g. using `werkzeug.security`) |

**Pages involved:** `login.html`  
**Routes involved:** `POST /login`, `GET /logout`

---

### 5.2 Dashboard Module

**Purpose:** The central hub a customer lands on after successful login.

| Concern | Behaviour |
|---|---|
| Balance Display | Fetch and render the customer's current balance |
| Navigation | Provide access to Deposit and Withdraw actions (buttons / forms on same page) |
| Session Context | Read customer identity from session to scope all data to the right account |
| Logout Link | Prominent link/button to end the session |

**Pages involved:** `dashboard.html`  
**Routes involved:** `GET /dashboard`

---

### 5.3 Account Management Module

**Purpose:** Expose read-only account information to the dashboard.

| Concern | Behaviour |
|---|---|
| Balance Retrieval | Query the database for the current balance of the logged-in customer |
| Account Context | Return account details (customer name, account number) for display |

**Routes involved:** Consumed internally by the Dashboard route; no separate endpoint needed.

---

### 5.4 Transactions Module

**Purpose:** Handle monetary operations against the account.

| Concern | Behaviour |
|---|---|
| Deposit | Accept an amount, validate it is a positive number, add to balance, record transaction |
| Withdrawal | Accept an amount, validate it is positive and ≤ current balance, deduct from balance, record transaction |
| Validation | Server-side enforcement of all rules; client-side pre-check for UX only |
| Feedback | Return success or descriptive error message to the dashboard |

**Pages involved:** `dashboard.html` (inline forms)  
**Routes involved:** `POST /deposit`, `POST /withdraw`

---

## 6. Implementation Roadmap

### Development Phases

```
Phase 1 — Project Scaffold
  ├─ Create FRONTEND/ and BACKEND/ folder structure
  ├─ Set up Python virtual environment and install Flask
  ├─ Create requirements.txt
  └─ Verify Flask app starts and serves a placeholder page
  Depends on: nothing

Phase 2 — Database Layer
  ├─ Implement database connection helper (db.py)
  ├─ Create seed script with at least two test customers
  └─ Confirm bank.db is created and queryable
  Depends on: Phase 1

Phase 3 — Authentication
  ├─ Build login route and login.html form
  ├─ Implement credential validation and session creation
  ├─ Implement logout route
  └─ Add session guard to protect all non-login routes
  Depends on: Phase 2

Phase 4 — Dashboard & Balance View
  ├─ Build dashboard route that reads balance from DB
  ├─ Render dashboard.html with customer name and balance
  └─ Verify redirect to login if not authenticated
  Depends on: Phase 3

Phase 5 — Deposit & Withdrawal
  ├─ Implement deposit route with validation and DB update
  ├─ Implement withdrawal route with balance-check and DB update
  ├─ Add inline forms to dashboard.html
  └─ Display success / error feedback on the dashboard
  Depends on: Phase 4

Phase 6 — Styling & Polish
  ├─ Apply Bootstrap layout to all pages (navbar, cards, alerts)
  ├─ Ensure responsive behaviour on mobile viewports
  └─ Final end-to-end manual test of all user flows
  Depends on: Phase 5
```

### Estimated Effort

| Phase | Effort |
|---|---|
| Phase 1 — Project Scaffold | Small |
| Phase 2 — Database Layer | Small |
| Phase 3 — Authentication | Medium |
| Phase 4 — Dashboard & Balance View | Small |
| Phase 5 — Deposit & Withdrawal | Medium |
| Phase 6 — Styling & Polish | Small |

### Dependencies Between Phases

```
Phase 1 ──▶ Phase 2 ──▶ Phase 3 ──▶ Phase 4 ──▶ Phase 5 ──▶ Phase 6
```

Each phase must be fully complete before the next phase begins. Phases are sequential
because each builds on the data access, session, and routing foundations established
in earlier phases.

---

*This document covers planning and architecture only. Database schema, SQL scripts,
API contracts, and step-by-step implementation details are out of scope for this document.*
