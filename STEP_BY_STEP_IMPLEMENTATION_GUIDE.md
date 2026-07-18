# Step-by-Step Implementation Guide — Banking Web Application

> **Reference Plan:** IMPLEMENTATION_PLAN.md  
> **Stack:** Python Flask · SQLite · HTML + Bootstrap  
> **Purpose:** Plain-English instructions explaining *what* to do and *why*, without full source code.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Integration Steps](#4-integration-steps)
5. [Validation Rules](#5-validation-rules)
6. [Testing](#6-testing)
7. [Deployment](#7-deployment)

---

## 1. Environment Setup

### 1.1 Prerequisites

Before writing a single line of code, make sure the following are installed on your machine:

- **Python 3.9 or higher** — Flask requires a modern Python version. Confirm by running `python --version` in your terminal.
- **pip** — Python's package manager, bundled with Python. Confirm with `pip --version`.
- A code editor (VS Code is recommended but not required).

### 1.2 Create the Project Folder Structure

Create the top-level project folder `banking-workshop/`. Inside it, create two sub-folders: `FRONTEND/` and `BACKEND/`. This separation keeps browser-facing code completely apart from server-side code and makes the project easy to navigate.

Inside `FRONTEND/`, create two more folders:
- `templates/` — for HTML pages that Flask will serve.
- `static/` — for any custom CSS or JavaScript files you want to ship locally.

Inside `BACKEND/`, create one sub-folder:
- `database/` — for the SQLite database file and the scripts that create and seed it.

### 1.3 Set Up a Python Virtual Environment

A virtual environment isolates your project's Python packages from anything else installed on your machine. This avoids version conflicts and keeps your project self-contained.

- Navigate into the `BACKEND/` folder in your terminal.
- Create a virtual environment there by running the standard Python command for creating one. Name it something clear like `venv`.
- Activate the virtual environment. On Windows the activation command lives in `venv\Scripts\activate`. On Mac/Linux it is `source venv/bin/activate`. Your terminal prompt will change to show the environment name when it is active.
- You should activate this environment every time you work on the project.

### 1.4 Install Flask and Dependencies

With the virtual environment active, install Flask using pip. Flask is the only mandatory external dependency for this project — it brings with it `Werkzeug` (for password hashing and WSGI utilities) and `Jinja2` (for HTML templating), both of which you will use.

After installation, create a file called `requirements.txt` inside `BACKEND/`. List each installed package and its version in that file. The standard way to do this is to run the pip freeze command and redirect its output into `requirements.txt`. This file lets anyone else (or a deployment server) reproduce your exact environment by running `pip install -r requirements.txt`.

### 1.5 Verify the Setup

Create a minimal `app.py` file inside `BACKEND/` that does nothing except start a Flask app and return the text "Hello, Bank!" on the root URL. Run it with `flask run` (or `python app.py`). If you see that message in your browser at `http://127.0.0.1:5000`, the environment is correctly configured and you can proceed.

---

## 2. Backend Implementation

### 2.1 Database Layer — `database/db.py`

This file is the single point of contact between all your Python code and the SQLite database. Nothing else should open a database connection directly.

**What it should do:**
- Hold the path to `bank.db` as a constant so you only ever change it in one place.
- Provide a function that opens a connection to SQLite and returns it. Configure the connection to return rows as dictionary-like objects (SQLite's `row_factory`) so you can access columns by name rather than by index — this makes the rest of the code far more readable.
- Provide a helper function that accepts a SQL query string and a tuple of parameters, executes the query safely using parameterised statements (never by string concatenation — that causes SQL injection), and returns the results.

**Why parameterised queries matter:** If you build SQL by concatenating user input directly into the query string, a malicious user can inject their own SQL commands. Parameterised queries pass the user input separately so the database engine treats it as data, never as SQL syntax.

### 2.2 Database Schema and Seeding — `database/seed.py`

The seed script runs once to create the database tables and insert test customer records. It is not part of the running application; you execute it manually before starting the server for the first time.

**Tables to create:**

- **`customers` table** — stores one row per registered customer. Columns: a unique integer ID (auto-generated primary key), a unique username string, a hashed password string, the customer's display name, and their current balance stored as a decimal number.
- **`transactions` table** — stores a record every time a deposit or withdrawal occurs. Columns: a unique integer ID, a foreign key linking to the `customers` table, a transaction type string (either "deposit" or "withdraw"), the amount involved, and a timestamp.

**Seeding logic:**
- Before inserting test customers, use `werkzeug.security.generate_password_hash()` to hash each customer's plain-text password. Never store plain-text passwords — always store the hash.
- Insert at least two test customer rows so you can verify that one customer cannot see another's data.
- The script should be safe to re-run: check whether the table already exists before creating it, or use `CREATE TABLE IF NOT EXISTS`.

### 2.3 Flask Application Entry Point — `app.py`

`app.py` is where Flask is initialised and all routes are registered. Think of it as the router directory for your application.

**What it should do:**
- Create the Flask app instance and point it at the correct `templates` folder (which lives in `FRONTEND/templates/`, not the default location). You do this by passing the `template_folder` argument when creating the app.
- Also point Flask at the correct `static` folder (`FRONTEND/static/`).
- Set a `SECRET_KEY` on the app. This key is used by Flask to cryptographically sign the session cookie. It must be a hard-to-guess string. For development you can use any string; for production it must come from an environment variable, not be hardcoded.
- Import and register all route functions (from `auth.py` and `account.py`).
- The `if __name__ == "__main__"` block at the bottom allows running the file directly for development.

### 2.4 Authentication Module — `auth.py`

This file handles everything related to proving and tracking a user's identity.

**Login route (`POST /login`):**
- Accept the form submission containing a username and password.
- Look up the customer row in the database by username.
- If no row is found, immediately return to the login page with a generic error like "Invalid username or password." Never say which one was wrong — that leaks information.
- If a row is found, use `werkzeug.security.check_password_hash()` to compare the submitted password against the stored hash. If they do not match, return the same generic error.
- On success, store the customer's ID in Flask's `session` dictionary. The session is server-side; the browser only receives a signed cookie that references it. Redirect the user to `/dashboard`.

**Logout route (`GET /logout`):**
- Call `session.clear()` to remove all session data.
- Redirect to the login page.

**Session guard (login-required decorator):**
- Write a reusable decorator function that any route can use to protect itself.
- The decorator checks whether the session contains a customer ID. If not, it redirects to `/login`. If it does, it allows the route to proceed normally.
- Apply this decorator to every route except `/login` itself.

### 2.5 Account Service — `account.py`

This file contains the business logic for reading and modifying account balances. It does not deal with HTTP requests directly — it receives already-validated data from routes and interacts with the database.

**Balance retrieval:**
- Accept a customer ID.
- Query the `customers` table for the row matching that ID.
- Return the balance and customer name for display on the dashboard.

**Deposit logic:**
- Accept a customer ID and an amount.
- Validate that the amount is a positive number greater than zero.
- Use a SQL `UPDATE` statement to add the amount to the customer's current balance.
- Insert a new row into the `transactions` table recording the deposit, the amount, and the current timestamp.
- Return a success indicator or raise an error if validation fails.

**Withdrawal logic:**
- Accept a customer ID and an amount.
- Validate that the amount is a positive number greater than zero.
- Query the current balance first.
- Check that the amount does not exceed the current balance. If it does, return an error — do not proceed with the update.
- Use a SQL `UPDATE` statement to subtract the amount from the balance.
- Insert a new row into the `transactions` table recording the withdrawal.
- Return a success indicator.

### 2.6 Dashboard and Transaction Routes — `app.py` additions

**Dashboard route (`GET /dashboard`):**
- Protected by the session guard decorator.
- Read the customer ID from the session.
- Call the account service to retrieve the customer's name and balance.
- Pass both to the `dashboard.html` template for rendering.

**Deposit route (`POST /deposit`):**
- Protected by the session guard decorator.
- Read the submitted amount from the form data.
- Convert it to a float. If conversion fails (non-numeric input), treat it as a validation error.
- Call the account service's deposit function.
- On success, redirect back to `/dashboard` so the refreshed balance is shown. Using a redirect after a POST prevents the browser from re-submitting the form if the user refreshes.
- On failure, re-render the dashboard with an error message.

**Withdrawal route (`POST /withdraw`):**
- Same structure as the deposit route, but calls the withdrawal function and carries the additional balance-check error case.

### 2.7 Error Handling

- Wrap route bodies in try/except blocks to catch unexpected database errors. Log them to the console (a simple `print` is fine for a workshop) and show a user-friendly "Something went wrong" message rather than a raw Python traceback.
- For all validation failures (bad amount, insufficient funds), return HTTP 400 with a clear human-readable message.
- Never let a raw Python exception reach the browser — this leaks implementation details.

### 2.8 Session Management Details

- Flask stores session data server-side and gives the browser a signed cookie as a reference key.
- The `SECRET_KEY` you set on the app signs the cookie to prevent tampering. If the key changes, all existing sessions are invalidated.
- By default, Flask sessions last until the browser is closed. For this project that is acceptable; for production you would set a `PERMANENT_SESSION_LIFETIME`.
- The session is a dictionary. Storing just the customer's integer ID is sufficient — you look up everything else from the database on each request using that ID.

---

## 3. Frontend Implementation

### 3.1 How Flask Serves HTML

Flask uses the Jinja2 template engine. HTML files placed in the `templates/` folder can contain special `{{ variable }}` placeholders that Flask replaces with real values before sending the page to the browser. They can also use `{% if %}` and `{% for %}` blocks for conditional content and loops. You pass variables in by calling `render_template("page.html", variable=value)` from the route.

### 3.2 Login Page — `templates/login.html`

This is the only page visible to unauthenticated users.

**Structure:**
- A centred card or panel (using Bootstrap's card component) containing the bank's name as a heading.
- A form with two fields: username (text input) and password (password input, which masks characters as the user types).
- A "Login" submit button.
- An area below (or above) the form where server-returned error messages are displayed. Wrap this in a Bootstrap alert component and only show it when an error message exists (use a Jinja2 `{% if %}` block around it).

**Form behaviour:**
- The form's `method` must be `POST` and its `action` must point to `/login`.
- Basic HTML5 validation attributes (`required`) on both inputs prevent submission with empty fields, giving instant feedback without a round trip to the server.

### 3.3 Dashboard Page — `templates/dashboard.html`

This is the main page an authenticated customer sees.

**Structure:**
- A top navigation bar (Bootstrap `navbar`) showing the bank name on the left and a "Logout" link on the right. The logout link should point to `/logout`.
- A welcome heading that includes the customer's name (passed in as a template variable).
- A prominent balance display card showing the current balance, formatted as currency.
- A feedback area for success and error messages — use Bootstrap alert colours (green for success, red for error). Only render this section when a message is present.
- Two side-by-side forms (use Bootstrap's grid with two columns on desktop, stacking to one column on mobile):
  - **Deposit form** — a numeric input for the amount and a "Deposit" button. The form posts to `/deposit`.
  - **Withdraw form** — a numeric input for the amount and a "Withdraw" button. The form posts to `/withdraw`.

**Template variables the route must supply:** customer name, current balance, and an optional message string (could be empty).

### 3.4 Bootstrap Layout Approach

Bootstrap is loaded from a CDN — add its stylesheet `<link>` tag in the `<head>` of every page and its JavaScript `<script>` tag just before the closing `</body>` tag. No local installation is needed.

Key Bootstrap concepts to use:
- **Container** (`class="container"`) — centres content horizontally and adds responsive padding.
- **Row and columns** (`class="row"` + `class="col-md-6"`) — creates a two-column layout on medium screens and wider, collapsing to a single column on small screens.
- **Card** (`class="card"`) — a bordered, padded panel, good for the login form and balance display.
- **Alert** (`class="alert alert-success"` or `class="alert alert-danger"`) — coloured feedback banners.
- **Navbar** (`class="navbar"`) — a responsive top navigation bar.
- **Button** (`class="btn btn-primary"`) — styled submit buttons.

### 3.5 Optional Custom Styles — `static/styles.css`

If Bootstrap's defaults are not quite right (for example, you want more vertical spacing between the balance card and the forms), add a `styles.css` file to `FRONTEND/static/` and link to it in your HTML after the Bootstrap CDN link. Keep overrides minimal — Bootstrap already provides most of what you need.

---

## 4. Integration Steps

### 4.1 Connect Flask to the Correct Template Folder

By default Flask looks for templates in a folder called `templates/` next to `app.py`. Because your templates live in `FRONTEND/templates/`, you must tell Flask where to look when creating the app instance. Pass the `template_folder` and `static_folder` arguments with the correct relative paths. Test this by running the app and confirming the login page loads with styles applied.

### 4.2 Connect Flask to SQLite

When a route needs data, it calls a function in `account.py` or `auth.py`. Those functions call the helper in `db.py` to open a connection, run a query, and return results. The connection should be opened at the start of a request and closed when the request finishes. Flask provides a `teardown_appcontext` hook for closing connections — register a function there that closes the database connection if one was opened during that request.

Alternatively (and more simply for this project), open and close the connection inside each individual service function. This is slightly less efficient but easier to reason about and perfectly acceptable at this scale.

### 4.3 Connect Frontend Forms to Flask Routes

Each HTML form specifies a `method` (GET or POST) and an `action` (the URL to submit to). The `name` attribute on each input field determines what key Flask sees in `request.form`. Make sure:

- The login form posts to `/login` with fields named `username` and `password`.
- The deposit form posts to `/deposit` with a field named `amount`.
- The withdraw form posts to `/withdraw` with a field named `amount`.

On the Flask side, read values using `request.form["fieldname"]`. If a field might be missing, use `request.form.get("fieldname")` which returns `None` instead of raising an error.

### 4.4 Pass Data from Flask to Templates

When calling `render_template()`, pass all the values the template needs as keyword arguments. For example, `render_template("dashboard.html", name=customer["name"], balance=customer["balance"], message=msg)`. In the template, reference these with `{{ name }}`, `{{ balance }}`, and `{{ message }}`.

To display currency nicely, you can apply Python's built-in string formatting: `"${:.2f}".format(balance)` before passing it to the template, or use a Jinja2 filter inline in the template itself.

### 4.5 Post-Redirect-Get Pattern

After every successful POST request (deposit or withdrawal), redirect the user to `GET /dashboard` rather than rendering the page directly. This is the Post-Redirect-Get (PRG) pattern. Without it, if the user refreshes the page after a deposit, the browser will re-submit the POST, causing a duplicate transaction. A redirect converts the response into a GET, so refreshing is harmless.

Use Flask's `redirect(url_for("dashboard"))` to do this.

---

## 5. Validation Rules

### 5.1 Login Validation

**Client-side (HTML):**
- Both the username and password fields must have the `required` attribute so the browser blocks submission of an empty form.
- No other client-side login validation is needed — the server makes the real decision.

**Server-side (Flask):**
- Check that both values are present in `request.form`. If either is missing or an empty string, reject immediately.
- Query the database for the username. If no matching row exists, return an error without revealing that the username was not found.
- Hash-compare the submitted password against the stored hash. If it does not match, return the same generic error.
- Only on both checks passing should a session be created.

### 5.2 Amount Validation for Deposit and Withdrawal

**Client-side (HTML):**
- The amount input should have `type="number"` and `min="0.01"` and `step="0.01"`. This prevents negative numbers and zero from being submitted and enforces two decimal places — but browser validation can always be bypassed, so it is a convenience only, not a security measure.
- The `required` attribute prevents empty submission.

**Server-side (Flask / account service):**
- Attempt to convert the submitted value to a float. If conversion raises an exception (the user submitted letters or a blank), treat it as invalid and return an error.
- Check that the converted value is strictly greater than zero. Zero and negative values are rejected.
- For withdrawals: query the current balance first and check that the requested amount does not exceed it. If it does, return a specific error like "Insufficient funds."

### 5.3 Session / Access Validation

- Every route except `/login` (the GET and POST) must be protected by the login-required decorator.
- The decorator checks for the presence of a customer ID in `session`. If it is absent, immediately redirect to `/login` without executing any route logic.
- After logout, `session.clear()` removes the customer ID so all subsequent requests are treated as unauthenticated.

### 5.4 Database-Level Integrity

- The `customers.balance` column should have a `CHECK (balance >= 0)` constraint defined in the `CREATE TABLE` statement. This is a last-resort safety net: even if a bug in the application logic fails to catch an overdraft, the database will reject the update and raise an error.
- The `transactions.amount` column should similarly have `CHECK (amount > 0)`.

---

## 6. Testing

### 6.1 Unit Tests

Unit tests verify individual functions in isolation, without starting the Flask server or touching a real database.

**What to unit test:**
- **Password hashing and verification** — confirm that hashing a plain-text password produces a different string, and that the check function correctly returns True for the right password and False for a wrong one.
- **Amount validation logic** — test the validation function in `account.py` directly with a variety of inputs: negative numbers, zero, non-numeric strings, very large numbers, and valid amounts. Confirm it returns the expected result for each.
- **Deposit calculation** — given a starting balance and a deposit amount, confirm the result is the sum of the two.
- **Withdrawal calculation** — given a starting balance, confirm a valid withdrawal reduces it correctly and an amount exceeding the balance is rejected.

Use Python's built-in `unittest` module or the `pytest` library (install via pip). Write each test as a function that calls the function under test and uses an assertion to verify the outcome.

### 6.2 Integration Tests

Integration tests verify that Flask routes, the service layer, and the database work together correctly.

**What to integration test:**
- **Login flow** — POST to `/login` with valid credentials; assert that the response redirects to `/dashboard` and that a session cookie is present.
- **Login failure** — POST to `/login` with a wrong password; assert that the response stays on the login page and contains an error message.
- **Dashboard access without login** — GET `/dashboard` without a session; assert that the response redirects to `/login`.
- **Deposit flow** — log in, then POST to `/deposit` with a valid amount; assert that the response redirects to `/dashboard` and that querying the database shows the updated balance.
- **Withdrawal flow** — log in, then POST to `/withdraw` with a valid amount; assert the balance decreases.
- **Overdraft prevention** — POST to `/withdraw` with an amount greater than the balance; assert that the balance is unchanged and an error is returned.

For integration tests use Flask's built-in test client (`app.test_client()`), which lets you simulate HTTP requests without a real network connection. Use a separate in-memory SQLite database (`:memory:`) or a test-specific `bank_test.db` file so tests do not corrupt your development data.

### 6.3 Manual Testing Checklist

Work through this checklist in the browser before considering the implementation complete:

**Authentication:**
- [ ] Visiting `/dashboard` while logged out redirects to `/login`.
- [ ] Submitting the login form with an empty username shows a validation error.
- [ ] Submitting the login form with an empty password shows a validation error.
- [ ] Submitting with a correct username and wrong password shows an error and stays on login.
- [ ] Submitting with a completely wrong username shows an error and stays on login.
- [ ] Submitting with correct credentials redirects to `/dashboard` and shows the customer name.
- [ ] Clicking "Logout" clears the session and redirects to `/login`.
- [ ] After logout, pressing the browser Back button does not regain access to the dashboard.

**Deposit:**
- [ ] Submitting a deposit with an empty amount shows a validation error.
- [ ] Submitting a deposit with a negative number shows a validation error.
- [ ] Submitting a deposit with zero shows a validation error.
- [ ] Submitting a deposit with a valid positive amount updates the displayed balance.
- [ ] The balance increase matches the deposited amount exactly.

**Withdrawal:**
- [ ] Submitting a withdrawal with an empty amount shows a validation error.
- [ ] Submitting a withdrawal with a negative number shows a validation error.
- [ ] Submitting a withdrawal with an amount larger than the balance shows "Insufficient funds."
- [ ] Submitting a withdrawal with a valid amount updates the displayed balance.
- [ ] The balance decrease matches the withdrawn amount exactly.

**Layout:**
- [ ] The login page is centred and readable on a desktop screen.
- [ ] The dashboard displays the balance clearly and both forms are visible without scrolling.
- [ ] The layout stacks sensibly on a narrow (mobile-width) browser window.

---

## 7. Deployment

### 7.1 Running Locally (Development)

This is the standard way to run during development and for the workshop demonstration:

1. Open a terminal and navigate to the `BACKEND/` folder.
2. Activate the virtual environment.
3. If you have not already done so, run the seed script once to create `bank.db` and populate test customers.
4. Run `flask run` (Flask reads the `FLASK_APP` environment variable to find `app.py`; set it to `app.py` if needed, or name the file `app.py` which Flask detects automatically).
5. Open a browser and go to `http://127.0.0.1:5000`.
6. Stop the server with `Ctrl + C` in the terminal.

Flask's development server includes an automatic reloader — when you save a Python file, the server restarts automatically so your changes take effect without manual restarts.

### 7.2 Environment Variables

Two values should never be hardcoded for production:

- **`SECRET_KEY`** — use a long random string stored in an environment variable, not in source code. In development you can leave a placeholder string, but understand the risk.
- **`FLASK_ENV`** or **`FLASK_DEBUG`** — in development, setting `FLASK_DEBUG=1` enables detailed error pages in the browser (useful for debugging). In production this must be off — it would expose your code internals to anyone who triggers an error.

### 7.3 Production Considerations

Flask's built-in development server is not suitable for production for the following reasons:
- It handles only one request at a time (no concurrency).
- Its automatic reloader and debug mode are security risks in a live environment.
- It is not hardened against malformed or malicious requests.

For a real production deployment:

- **Use a production WSGI server** such as `gunicorn` (Linux/Mac) or `waitress` (Windows-compatible). Both are installed via pip and wrap your Flask app to handle multiple simultaneous requests.
- **Use a reverse proxy** such as Nginx in front of the WSGI server. Nginx handles serving static files efficiently and provides TLS termination (HTTPS).
- **Move the database** from SQLite to a proper server-based database (PostgreSQL or MySQL) if the application will serve more than a handful of concurrent users, since SQLite has limited write concurrency.
- **Store secrets in environment variables** or a secrets manager — never in source code or committed to a repository.
- **Enable HTTPS** so credentials are never transmitted as plain text.

For this workshop, the local development server is the intended runtime and none of the above steps are required to complete the project.

---

*This guide covers implementation logic and decisions. It does not provide copy-paste source code — the goal is for you to understand each component well enough to build it yourself.*
