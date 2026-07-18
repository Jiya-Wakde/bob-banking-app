"""
account.py — Account service: balance retrieval, deposit, and withdrawal.

All business rules for monetary operations live here. Routes in app.py delegate
to these functions after performing basic request parsing.
"""

from database.db import query_db


class AccountError(Exception):
    """Raised for validation failures or business-rule violations."""
    pass


# ---------------------------------------------------------------------------
# Balance / account info
# ---------------------------------------------------------------------------

def get_account(customer_id):
    """
    Return a dict with 'name' and 'balance' for the given customer_id.
    Returns None if the customer does not exist.
    """
    return query_db(
        "SELECT name, balance FROM customers WHERE id = ?",
        (customer_id,),
        one=True,
    )


# ---------------------------------------------------------------------------
# Deposit
# ---------------------------------------------------------------------------

def deposit(customer_id, raw_amount):
    """
    Add *raw_amount* to the customer's balance and record the transaction.

    Args:
        customer_id – integer, taken from session.
        raw_amount  – value as submitted via the form (string or number).

    Returns:
        The new balance as a float.

    Raises:
        AccountError – if the amount is invalid (non-numeric, zero, or negative).
    """
    amount = _parse_positive_amount(raw_amount)

    query_db(
        "UPDATE customers SET balance = balance + ? WHERE id = ?",
        (amount, customer_id),
        commit=True,
    )
    query_db(
        "INSERT INTO transactions (customer_id, type, amount) VALUES (?, 'deposit', ?)",
        (customer_id, amount),
        commit=True,
    )

    account = get_account(customer_id)
    return account["balance"]


# ---------------------------------------------------------------------------
# Withdrawal
# ---------------------------------------------------------------------------

def withdraw(customer_id, raw_amount):
    """
    Deduct *raw_amount* from the customer's balance and record the transaction.

    Args:
        customer_id – integer, taken from session.
        raw_amount  – value as submitted via the form (string or number).

    Returns:
        The new balance as a float.

    Raises:
        AccountError – if the amount is invalid or exceeds the current balance.
    """
    amount = _parse_positive_amount(raw_amount)

    account = get_account(customer_id)
    if account is None:
        raise AccountError("Account not found.")

    if amount > account["balance"]:
        raise AccountError(
            f"Insufficient funds. Your current balance is ${account['balance']:.2f}."
        )

    query_db(
        "UPDATE customers SET balance = balance - ? WHERE id = ?",
        (amount, customer_id),
        commit=True,
    )
    query_db(
        "INSERT INTO transactions (customer_id, type, amount) VALUES (?, 'withdraw', ?)",
        (customer_id, amount),
        commit=True,
    )

    account = get_account(customer_id)
    return account["balance"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_positive_amount(raw):
    """
    Convert *raw* to a float and assert it is strictly positive.

    Raises AccountError for non-numeric, zero, or negative values.
    """
    try:
        amount = float(raw)
    except (TypeError, ValueError):
        raise AccountError("Please enter a valid numeric amount.")

    if amount <= 0:
        raise AccountError("Amount must be greater than zero.")

    return amount
