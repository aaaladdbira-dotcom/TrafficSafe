
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import requests
import os
from werkzeug.utils import secure_filename
from models.user import User
from models.accident import Accident

register_ui = Blueprint("register_ui", __name__)


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


def get_live_stats():
    """Get live statistics for the register page"""
    try:
        user_count = User.query.count()
        accident_count = Accident.query.count()
        
        # Format user count: round down to nearest 100, add +
        if user_count >= 1000:
            user_display = f"{(user_count // 100) * 100 - 100}+"
        elif user_count >= 100:
            user_display = f"{(user_count // 10) * 10 - 10}+"
        else:
            user_display = f"{max(user_count - 1, 0)}+"
        
        # Format accident count
        if accident_count >= 10000:
            accident_display = f"{accident_count // 1000}K+"
        elif accident_count >= 1000:
            accident_display = f"{(accident_count // 100) / 10:.1f}K+".replace('.0', '')
        else:
            accident_display = f"{accident_count}+"
        
        return {
            'users': user_display,
            'reports': accident_display,
            'governorates': '24'
        }
    except Exception:
        return {
            'users': '100+',
            'reports': '1K+',
            'governorates': '24'
        }

@register_ui.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        gender = request.form.get("gender")
        date_of_birth = request.form.get("date_of_birth")
        user_type = request.form.get("user_type")
        email = request.form.get("email")
        password = request.form.get("password")
        national_id = request.form.get("national_id")
        work_place = request.form.get("work_place")
        badge_number = request.form.get("badge_number")
        journalist_id = request.form.get("journalist_id")
        avatar_file = request.files.get("avatar")

        avatar_url = None
        if avatar_file and avatar_file.filename:
            filename = secure_filename(email + "_" + avatar_file.filename)
            avatar_dir = os.path.join(current_app.root_path, "static", "avatars")
            os.makedirs(avatar_dir, exist_ok=True)
            avatar_path = os.path.join(avatar_dir, filename)
            avatar_file.save(avatar_path)
            avatar_url = f"/static/avatars/{filename}"

        # Build registration payload
        payload = {
            "full_name": full_name,
            "gender": gender,
            "date_of_birth": date_of_birth,
            "email": email,
            "password": password,
            "user_type": user_type,
            "national_id": national_id,
            "work_place": work_place if user_type in ["police", "media"] else None,
            "badge_number": badge_number if user_type == "police" else None,
            "journalist_id": journalist_id if user_type == "media" else None,
            "avatar_url": avatar_url,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            resp = call_api("/api/v1/auth/register", method='POST', json=payload, timeout=5)
        except Exception:
            flash("API not reachable", "danger")
            return render_template("register.html", stats=get_live_stats())

        if resp.status_code != 201:
            try:
                msg = resp.json().get("message", "Registration failed")
            except Exception:
                msg = "Registration failed. Please check your input or try again."
            flash(msg, "danger")
            return render_template("register.html", stats=get_live_stats())

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth_ui.login"))

    stats = get_live_stats()
    return render_template("register.html", stats=stats)
