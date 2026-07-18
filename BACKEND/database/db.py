"""
database/db.py — Single point of contact between application code and SQLite.

All database operations go through get_connection() or query_db(). Never open a
connection anywhere else in the codebase.
"""

import sqlite3
import os

# Absolute path to bank.db, resolved relative to this file so the app can be
# started from any working directory.
DB_PATH = os.path.join(os.path.dirname(__file__), "bank.db")


def get_connection():
    """Open and return a SQLite connection with dict-style row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # columns accessible by name, e.g. row["balance"]
    conn.execute("PRAGMA foreign_keys = ON")  # enforce FK constraints
    return conn


def query_db(sql, params=(), one=False, commit=False):
    """
    Execute *sql* with *params* using a parameterised statement (prevents SQL
    injection) and return the results.

    Args:
        sql     – SQL string with ? placeholders.
        params  – tuple of values to bind to the placeholders.
        one     – if True, return a single row dict (or None); otherwise return
                  a list of row dicts.
        commit  – if True, commit the transaction (needed for INSERT/UPDATE/DELETE).

    Returns:
        A single dict, a list of dicts, or None.
    """
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        if commit:
            conn.commit()
            return cur.lastrowid   # useful for INSERT callers
        rows = cur.fetchone() if one else cur.fetchall()
        # Convert sqlite3.Row objects to plain dicts for easier downstream use
        if one:
            return dict(rows) if rows else None
        return [dict(r) for r in rows]
    finally:
        conn.close()
