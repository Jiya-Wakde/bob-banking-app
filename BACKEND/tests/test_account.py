"""
tests/test_account.py — Unit tests for account service logic.

Run from the BACKEND/ directory with:
    pytest tests/ -v
"""

import sys
import os

# Make the BACKEND source importable when pytest is run from BACKEND/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from account import AccountError, _parse_positive_amount, deposit, get_account, withdraw
from database.db import get_connection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_test_db(conn):
    """Create schema in an in-memory SQLite database."""
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
        ("testuser", "hashed", "Test User", 1000.0),
    )
    conn.commit()
    return conn.execute("SELECT id FROM customers WHERE username='testuser'").fetchone()[0]


# ---------------------------------------------------------------------------
# Unit tests — _parse_positive_amount
# ---------------------------------------------------------------------------

class TestParseAmount:

    def test_valid_integer_string(self):
        assert _parse_positive_amount("100") == 100.0

    def test_valid_float_string(self):
        assert _parse_positive_amount("49.99") == pytest.approx(49.99)

    def test_valid_numeric_type(self):
        assert _parse_positive_amount(250) == 250.0

    def test_zero_rejected(self):
        with pytest.raises(AccountError):
            _parse_positive_amount("0")

    def test_negative_rejected(self):
        with pytest.raises(AccountError):
            _parse_positive_amount("-10")

    def test_non_numeric_string_rejected(self):
        with pytest.raises(AccountError):
            _parse_positive_amount("abc")

    def test_empty_string_rejected(self):
        with pytest.raises(AccountError):
            _parse_positive_amount("")

    def test_none_rejected(self):
        with pytest.raises(AccountError):
            _parse_positive_amount(None)


# ---------------------------------------------------------------------------
# Integration tests — deposit and withdraw (using a real temp DB)
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """
    Create a temporary bank.db, monkeypatch DB_PATH so account functions use it,
    and yield the customer_id of the test account.
    """
    import database.db as db_module

    test_db = str(tmp_path / "bank_test.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db)

    conn = get_connection()
    customer_id = _setup_test_db(conn)
    conn.close()
    return customer_id


class TestDeposit:

    def test_deposit_increases_balance(self, db_path):
        customer_id = db_path
        new_balance = deposit(customer_id, "200")
        assert new_balance == pytest.approx(1200.0)

    def test_deposit_records_transaction(self, db_path):
        customer_id = db_path
        deposit(customer_id, "50")
        from database.db import query_db
        txns = query_db(
            "SELECT * FROM transactions WHERE customer_id=? AND type='deposit'",
            (customer_id,),
        )
        assert len(txns) == 1
        assert txns[0]["amount"] == pytest.approx(50.0)

    def test_deposit_zero_raises(self, db_path):
        with pytest.raises(AccountError):
            deposit(db_path, "0")

    def test_deposit_negative_raises(self, db_path):
        with pytest.raises(AccountError):
            deposit(db_path, "-100")

    def test_deposit_text_raises(self, db_path):
        with pytest.raises(AccountError):
            deposit(db_path, "fifty dollars")


class TestWithdraw:

    def test_withdraw_decreases_balance(self, db_path):
        customer_id = db_path
        new_balance = withdraw(customer_id, "300")
        assert new_balance == pytest.approx(700.0)

    def test_withdraw_records_transaction(self, db_path):
        customer_id = db_path
        withdraw(customer_id, "100")
        from database.db import query_db
        txns = query_db(
            "SELECT * FROM transactions WHERE customer_id=? AND type='withdraw'",
            (customer_id,),
        )
        assert len(txns) == 1
        assert txns[0]["amount"] == pytest.approx(100.0)

    def test_withdraw_exact_balance_allowed(self, db_path):
        customer_id = db_path
        new_balance = withdraw(customer_id, "1000")
        assert new_balance == pytest.approx(0.0)

    def test_withdraw_exceeds_balance_raises(self, db_path):
        with pytest.raises(AccountError, match="Insufficient funds"):
            withdraw(db_path, "9999")

    def test_withdraw_zero_raises(self, db_path):
        with pytest.raises(AccountError):
            withdraw(db_path, "0")

    def test_withdraw_negative_raises(self, db_path):
        with pytest.raises(AccountError):
            withdraw(db_path, "-50")
