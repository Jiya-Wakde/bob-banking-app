"""
auth.py — Authentication helpers: login, logout, session guard decorator.

Imported by app.py and used to register /login and /logout routes, plus
the @login_required decorator that protects every other route.
"""

from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from database.db import query_db

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Session guard decorator
# ---------------------------------------------------------------------------

def login_required(f):
    """
    Decorator that redirects unauthenticated requests to /login.

    Usage::

        @app.route("/dashboard")
        @login_required
        def dashboard():
            ...
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "customer_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Render the login form (GET) and authenticate the submitted credentials (POST)."""
    # If already logged in, skip the login page
    if "customer_id" in session:
        return redirect(url_for("main.dashboard"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Server-side presence check (client-side required= is a convenience only)
        if not username or not password:
            error = "Username and password are required."
        else:
            customer = query_db(
                "SELECT * FROM customers WHERE username = ?",
                (username,),
                one=True,
            )

            # Generic error — never reveal which field was wrong
            if customer is None or not check_password_hash(customer["password"], password):
                error = "Invalid username or password."
            else:
                session.clear()
                session["customer_id"] = customer["id"]
                return redirect(url_for("main.dashboard"))

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    """Destroy the session and redirect to login."""
    session.clear()
    return redirect(url_for("auth.login"))
