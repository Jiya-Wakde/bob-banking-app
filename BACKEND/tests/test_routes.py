"""
tests/test_routes.py — Integration tests for Flask routes using the test client.

Run from the BACKEND/ directory with:
    pytest tests/ -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import database.db as db_module
from werkzeug.security import generate_password_hash
from app import app as flask_app
from database.db import get_connection


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Provide a Flask test client wired to an isolated in-memory database.
    A single test customer (id=1, alice/password123, balance=500) is seeded.
    """
    test_db = str(tmp_path / "test_bank.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db)

    conn = get_connection()
    conn.executescript("""
        CREATE TABLE customers (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            name     TEXT    NOT NULL,
            balance  REAL    NOT NULL DEFAULT 0.0 CHECK (balance >= 0)
        );
        CREATE TABLE transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            type        TEXT    NOT NULL CHECK (type IN ('deposit', 'withdraw')),
            amount      REAL    NOT NULL CHECK (amount > 0),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.execute(
        "INSERT INTO customers (username, password, name, balance) VALUES (?, ?, ?, ?)",
        ("alice", generate_password_hash("password123"), "Alice Johnson", 500.0),
    )
    conn.commit()
    conn.close()

    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    with flask_app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def login(client, username="alice", password="password123"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


# ---------------------------------------------------------------------------
# Authentication route tests
# ---------------------------------------------------------------------------

class TestLogin:

    def test_login_page_loads(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"Sign in" in resp.data

    def test_valid_login_redirects_to_dashboard(self, client):
        resp = login(client)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_wrong_password_shows_error(self, client):
        resp = client.post(
            "/login",
            data={"username": "alice", "password": "wrongpass"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_unknown_username_shows_error(self, client):
        resp = client.post(
            "/login",
            data={"username": "nobody", "password": "anything"},
            follow_redirects=True,
        )
        assert b"Invalid username or password" in resp.data

    def test_empty_credentials_show_error(self, client):
        resp = client.post(
            "/login",
            data={"username": "", "password": ""},
            follow_redirects=True,
        )
        assert b"required" in resp.data


class TestLogout:

    def test_logout_clears_session(self, client):
        login(client)
        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        # After logout, /dashboard must redirect to /login
        resp2 = client.get("/dashboard", follow_redirects=False)
        assert "/login" in resp2.headers["Location"]


# ---------------------------------------------------------------------------
# Session guard tests
# ---------------------------------------------------------------------------

class TestSessionGuard:

    def test_dashboard_without_login_redirects(self, client):
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_deposit_without_login_redirects(self, client):
        resp = client.post("/deposit", data={"amount": "100"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_withdraw_without_login_redirects(self, client):
        resp = client.post("/withdraw", data={"amount": "50"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# Dashboard tests
# ---------------------------------------------------------------------------

class TestDashboard:

    def test_dashboard_shows_name_and_balance(self, client):
        login(client)
        resp = client.get("/dashboard", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Alice" in resp.data
        assert b"500.00" in resp.data


# ---------------------------------------------------------------------------
# Deposit route tests
# ---------------------------------------------------------------------------

class TestDepositRoute:

    def test_valid_deposit_redirects(self, client):
        login(client)
        resp = client.post("/deposit", data={"amount": "100"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_valid_deposit_updates_balance(self, client):
        login(client)
        client.post("/deposit", data={"amount": "250"})
        resp = client.get("/dashboard", follow_redirects=True)
        assert b"750.00" in resp.data

    def test_deposit_zero_shows_error(self, client):
        login(client)
        resp = client.post("/deposit", data={"amount": "0"}, follow_redirects=True)
        assert b"greater than zero" in resp.data

    def test_deposit_negative_shows_error(self, client):
        login(client)
        resp = client.post("/deposit", data={"amount": "-50"}, follow_redirects=True)
        assert b"greater than zero" in resp.data

    def test_deposit_text_shows_error(self, client):
        login(client)
        resp = client.post("/deposit", data={"amount": "abc"}, follow_redirects=True)
        assert b"valid numeric" in resp.data


# ---------------------------------------------------------------------------
# Withdrawal route tests
# ---------------------------------------------------------------------------

class TestWithdrawRoute:

    def test_valid_withdraw_redirects(self, client):
        login(client)
        resp = client.post("/withdraw", data={"amount": "100"}, follow_redirects=False)
        assert resp.status_code == 302

    def test_valid_withdraw_updates_balance(self, client):
        login(client)
        client.post("/withdraw", data={"amount": "200"})
        resp = client.get("/dashboard", follow_redirects=True)
        assert b"300.00" in resp.data

    def test_overdraft_shows_error(self, client):
        login(client)
        resp = client.post("/withdraw", data={"amount": "9999"}, follow_redirects=True)
        assert b"Insufficient funds" in resp.data

    def test_overdraft_does_not_change_balance(self, client):
        login(client)
        client.post("/withdraw", data={"amount": "9999"})
        resp = client.get("/dashboard", follow_redirects=True)
        assert b"500.00" in resp.data

    def test_withdraw_zero_shows_error(self, client):
        login(client)
        resp = client.post("/withdraw", data={"amount": "0"}, follow_redirects=True)
        assert b"greater than zero" in resp.data
