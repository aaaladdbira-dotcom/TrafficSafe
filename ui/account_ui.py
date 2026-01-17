from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
from extensions import db
from models.user import User

account_ui = Blueprint("account_ui", __name__)

def get_current_user():
    email = session.get("email")
    if not email:
        return None
    return User.query.filter_by(email=email).first()

@account_ui.route("/account-settings", methods=["GET", "POST"])
def account_settings():
    user = get_current_user()
    if not user:
        next_url = request.url
        flash("User not found or not logged in.", "danger")
        return redirect(url_for("auth_ui.login", next=next_url))


    if request.method == "POST":
        # Profile fields
        user.full_name = request.form.get("full_name", user.full_name)
        session["name"] = user.full_name
        user.email = request.form.get("email", user.email)
        session["email"] = user.email
        user.gender = request.form.get("gender", user.gender)
        user.date_of_birth = request.form.get("date_of_birth", user.date_of_birth)
        user.national_id = request.form.get("national_id", user.national_id)

        # Password
        password = request.form.get("new_password")
        if password:
            user.password_hash = generate_password_hash(password)

        # Avatar
        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            filename = secure_filename(avatar_file.filename)
            avatar_path = os.path.join(current_app.root_path, "static", "avatars")
            os.makedirs(avatar_path, exist_ok=True)
            file_path = os.path.join(avatar_path, filename)
            avatar_file.save(file_path)
            user.avatar_url = f"/static/avatars/{filename}"
            session["avatar_url"] = user.avatar_url

        # Theme and UI settings
        user.dark_mode = "dark_mode" in request.form
        session["dark_mode"] = user.dark_mode
        # Removed font_size, table_density, date_format, reduce_animations (not in User model)

        # Notification settings
        user.email_notifications = bool(request.form.get("email_notifications"))
        user.sms_alerts = bool(request.form.get("sms_alerts"))
        user.system_alerts = bool(request.form.get("system_alerts"))
        user.newsletter = bool(request.form.get("newsletter"))
        user.report_status_updates = bool(request.form.get("report_status_updates"))
        user.gov_announcements = bool(request.form.get("gov_announcements"))
        user.dnd_mode = bool(request.form.get("dnd_mode"))
        user.sound_alerts = bool(request.form.get("sound_alerts"))
        user.vibration_alerts = bool(request.form.get("vibration_alerts"))

        # Save changes
        db.session.commit()
        # Reload user from DB to get latest values
        user = User.query.filter_by(email=user.email).first()
        flash("Settings updated successfully!", "success")
        return redirect(url_for("account_ui.account_settings"))

    # Prepare user dict for template
    user_dict = {
        # Map 'name' to 'full_name' for template compatibility
        "full_name": getattr(user, "full_name", None) or getattr(user, "name", None) or "–",
        "email": getattr(user, "email", None) or "–",
        "gender": getattr(user, "gender", None) or "–",
        "date_of_birth": str(getattr(user, "date_of_birth", None)) if getattr(user, "date_of_birth", None) else "–",
        "national_id": getattr(user, "national_id", None) or "–",
        "role": getattr(user, "role", None),
        "avatar_url": getattr(user, "avatar_url", None),
        "dark_mode": getattr(user, "dark_mode", False),
        "created_at": getattr(user, "created_at", None),
        # Add notification and settings fields as needed
        "email_notifications": getattr(user, "email_notifications", False),
        "sms_alerts": getattr(user, "sms_alerts", False),
        "system_alerts": getattr(user, "system_alerts", False),
        "newsletter": getattr(user, "newsletter", False),
        "report_status_updates": getattr(user, "report_status_updates", False),
        "gov_announcements": getattr(user, "gov_announcements", False),
    "dnd_mode": getattr(user, "dnd_mode", False),
        "sound_alerts": getattr(user, "sound_alerts", False),
        "vibration_alerts": getattr(user, "vibration_alerts", False),
    }
    print("[DEBUG] user_dict for account_settings:", user_dict)
    next_url = request.args.get("next")
    return render_template("account_settings.html", user=user_dict, next=next_url)


@account_ui.route("/preferences", methods=["PATCH"])
def update_preferences():
    """Instant preference update endpoint for AJAX calls"""
    from flask import jsonify
    
    user = get_current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    updated_fields = []
    
    # Only allow specific preference fields
    allowed_preferences = ['dark_mode', 'email_notifications', 'sms_alerts', 'system_alerts']
    
    for field in allowed_preferences:
        if field in data:
            setattr(user, field, bool(data[field]))
            updated_fields.append(field)
            # Also update session for dark_mode
            if field == 'dark_mode':
                session['dark_mode'] = bool(data[field])
    
    if updated_fields:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Preferences updated',
            'updated': updated_fields
        })
    
    return jsonify({"error": "No valid preference fields to update."}), 400

