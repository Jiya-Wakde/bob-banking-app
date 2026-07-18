"""
app.py — Flask application entry point.

Creates the app instance, wires up the template/static folders (which live
inside FRONTEND/ rather than next to this file), registers Blueprints, and
defines the protected application routes.

Run with:
    cd BACKEND
    flask run          (Flask auto-detects app.py)
  or
    python app.py
"""

import os

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from auth import auth_bp, login_required
from account import AccountError, deposit, get_account, withdraw

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "FRONTEND")

app = __import__("flask").Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static"),
)

# SECRET_KEY signs the session cookie. In production this MUST come from an
# environment variable (never committed to source control).
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

# ---------------------------------------------------------------------------
# Register Blueprints
# ---------------------------------------------------------------------------

app.register_blueprint(auth_bp)

# ---------------------------------------------------------------------------
# Main Blueprint — dashboard and transaction routes
# ---------------------------------------------------------------------------

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Root URL: redirect to dashboard (session guard handles auth check)."""
    return redirect(url_for("main.dashboard"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Render the account dashboard with the current balance."""
    customer_id = session["customer_id"]
    try:
        account = get_account(customer_id)
    except Exception as exc:
        print(f"[dashboard] DB error: {exc}")
        account = None

    if account is None:
        session.clear()
        return redirect(url_for("auth.login"))

    return render_template(
        "dashboard.html",
        name=account["name"],
        balance=account["balance"],
        message=request.args.get("message", ""),
        message_type=request.args.get("message_type", "success"),
    )


@main_bp.route("/deposit", methods=["POST"])
@login_required
def deposit_route():
    """Accept a deposit form submission, update the balance, redirect to dashboard."""
    customer_id = session["customer_id"]
    raw_amount = request.form.get("amount", "")

    try:
        new_balance = deposit(customer_id, raw_amount)
        return redirect(
            url_for(
                "main.dashboard",
                message=f"Deposit successful. New balance: ${new_balance:.2f}",
                message_type="success",
            )
        )
    except AccountError as exc:
        return redirect(
            url_for("main.dashboard", message=str(exc), message_type="danger")
        )
    except Exception as exc:
        print(f"[deposit] Unexpected error: {exc}")
        return redirect(
            url_for(
                "main.dashboard",
                message="Something went wrong. Please try again.",
                message_type="danger",
            )
        )


@main_bp.route("/withdraw", methods=["POST"])
@login_required
def withdraw_route():
    """Accept a withdrawal form submission, update the balance, redirect to dashboard."""
    customer_id = session["customer_id"]
    raw_amount = request.form.get("amount", "")

    try:
        new_balance = withdraw(customer_id, raw_amount)
        return redirect(
            url_for(
                "main.dashboard",
                message=f"Withdrawal successful. New balance: ${new_balance:.2f}",
                message_type="success",
            )
        )
    except AccountError as exc:
        return redirect(
            url_for("main.dashboard", message=str(exc), message_type="danger")
        )
    except Exception as exc:
        print(f"[withdraw] Unexpected error: {exc}")
        return redirect(
            url_for(
                "main.dashboard",
                message="Something went wrong. Please try again.",
                message_type="danger",
            )
        )


app.register_blueprint(main_bp)

# ---------------------------------------------------------------------------
# Dev server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
