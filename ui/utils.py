from functools import wraps
from flask import session, redirect, url_for

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "access_token" not in session:
            return redirect(url_for("auth_ui.login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "access_token" not in session:
                return redirect(url_for("auth_ui.login"))
            if session.get("role") != role:
                return redirect(url_for("dashboard_ui.dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator
