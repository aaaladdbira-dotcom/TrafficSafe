from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
import requests
from extensions import db
from models.user import User

auth_ui = Blueprint("auth_ui", __name__, url_prefix="/ui")


def call_api(endpoint, method='GET', headers=None, params=None, json=None, timeout=5):
    """Call API endpoint - either via HTTP or internal WSGI client.
    
    If API_URL is configured, use requests for external API.
    Otherwise, use Flask test client for internal routing.
    """
    api_base = current_app.config.get('API_URL', '')
    
    if api_base:
        # External API - use requests
        url = f"{api_base}{endpoint}"
        try:
            if method.upper() == 'GET':
                return requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == 'POST':
                return requests.post(url, headers=headers, params=params, json=json, timeout=timeout)
            else:
                return requests.request(method, url, headers=headers, params=params, json=json, timeout=timeout)
        except Exception as e:
            class FakeResponse:
                def __init__(self, error):
                    self.status_code = 502
                    self.text = str(error)
                def json(self):
                    raise ValueError("No JSON")
            return FakeResponse(e)
    else:
        # Internal WSGI call - use Flask test client
        try:
            client = current_app.test_client()
            query_string = ''
            if params:
                query_string = '?' + '&'.join(f"{k}={v}" for k, v in params.items() if v)
            
            if method.upper() == 'GET':
                resp = client.get(endpoint + query_string, headers=headers)
            elif method.upper() == 'POST':
                resp = client.post(endpoint + query_string, headers=headers, json=json)
            else:
                resp = client.open(endpoint + query_string, method=method, headers=headers, json=json)
            
            return resp
        except Exception as e:
            class FakeResponse:
                def __init__(self, error):
                    self.status_code = 502
                    self.text = str(error)
                def json(self):
                    raise ValueError("No JSON")
            return FakeResponse(e)


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
            resp = call_api("/api/v1/auth/login", method='POST', json={"email": email, "password": password}, timeout=5)
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
