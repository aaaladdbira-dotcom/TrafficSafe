from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import requests
from extensions import db
from models.user import User

auth_ui = Blueprint("auth_ui", __name__, url_prefix="/ui")


@auth_ui.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next")
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Prefer next from POST if present
        next_post = request.form.get("next")
        if next_post:
            next_url = next_post

        # Call API login
        try:
            resp = requests.post(
                "http://127.0.0.1:5001/api/v1/auth/login",
                json={"email": email, "password": password},
                timeout=5,
            )
        except Exception:
            flash("API not reachable", "danger")
            return render_template("login.html", next=next_url)

        if resp.status_code != 200:
            flash("Invalid email or password", "danger")
            return render_template("login.html", next=next_url)

        data = resp.json()

        # 🔑 STORE AUTH DATA IN SESSION
        session["access_token"] = data["access_token"]
        session["role"] = data["role"]
        session["email"] = email

        # Load user preferences from database
        user = User.query.filter_by(email=email).first()
        if user:
            session["dark_mode"] = user.dark_mode
            session["name"] = user.full_name

        # ✅ REDIRECT TO intended page or dashboard
        if next_url:
            return redirect(next_url)
        return redirect(url_for("dashboard_ui.dashboard"))

    return render_template("login.html", next=next_url)


@auth_ui.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth_ui.login"))
