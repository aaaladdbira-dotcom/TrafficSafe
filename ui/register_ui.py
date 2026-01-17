
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import requests
import os
from werkzeug.utils import secure_filename
from models.user import User
from models.accident import Accident

register_ui = Blueprint("register_ui", __name__)

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
            resp = requests.post(
                "http://127.0.0.1:5001/api/v1/auth/register",
                json=payload,
                timeout=5,
            )
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
