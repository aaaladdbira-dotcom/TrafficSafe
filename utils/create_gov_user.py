import secrets
from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User

def create_government_user():
    # Only create if no users exist
    if User.query.first() is None:
        email = "admin@traffic.gov.tn"
        password = secrets.token_urlsafe(12)
        user = User(
            name="Government Admin",
            email=email,
            password_hash=generate_password_hash(password),
            role="government",
            national_id="00000000",
            user_type="government",
            work_place=None,
            badge_number=None,
            journalist_id=None,
        )
        db.session.add(user)
        db.session.commit()
        print(f"Government admin created. Email: {email} Password: {password}")
    else:
        print("Users already exist. No government admin created.")
