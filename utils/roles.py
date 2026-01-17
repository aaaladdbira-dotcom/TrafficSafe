from flask_jwt_extended import get_jwt
from functools import wraps
from flask import abort

def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role")

            if user_role != required_role:
                abort(403, description="Forbidden: insufficient role")

            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Shortcut for government role
government_required = role_required("government")
