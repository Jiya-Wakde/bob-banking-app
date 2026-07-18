"""
database/seed.py — Creates the schema and seeds two test customer accounts.

Run this script once before starting the Flask server:
    cd BACKEND
    python database/seed.py

It is safe to re-run: CREATE TABLE IF NOT EXISTS guards against duplicate schema,
and the INSERT is skipped when the username already exists.
"""

import sys
import os

# Allow importing db.py regardless of which directory the script is invoked from
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from werkzeug.security import generate_password_hash
from database.db import get_connection


def create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            name     TEXT    NOT NULL,
            balance  REAL    NOT NULL DEFAULT 0.0
                             CHECK (balance >= 0)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            type        TEXT    NOT NULL CHECK (type IN ('deposit', 'withdraw')),
            amount      REAL    NOT NULL CHECK (amount > 0),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


def seed_customers(conn):
    """Insert test accounts only if they don't already exist."""
    test_customers = [
        {
            "username": "alice",
            "password": "password123",
            "name": "Alice Johnson",
            "balance": 2500.00,
        },
        {
            "username": "bob",
            "password": "securepass",
            "name": "Bob Smith",
            "balance": 750.50,
        },
    ]

    for c in test_customers:
        existing = conn.execute(
            "SELECT id FROM customers WHERE username = ?", (c["username"],)
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO customers (username, password, name, balance) VALUES (?, ?, ?, ?)",
                (
                    c["username"],
                    generate_password_hash(c["password"]),
                    c["name"],
                    c["balance"],
                ),
            )
            print(f"  Seeded customer: {c['username']} (balance: {c['balance']:.2f})")
        else:
            print(f"  Skipped (already exists): {c['username']}")

    conn.commit()


if __name__ == "__main__":
    print("=== Banking Workshop — DB Seed ===")
    conn = get_connection()
    try:
        create_tables(conn)
        print("Tables created (or already existed).")
        seed_customers(conn)
        print("Done. bank.db is ready.")
    finally:
        conn.close()
