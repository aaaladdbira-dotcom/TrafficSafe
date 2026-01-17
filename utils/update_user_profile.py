# Script to update a user's profile information in the database
# Usage: Run with `flask shell` or as a standalone script if your app context is set up

from app import app
from models import db
from models.user import User

# Update these values as needed
target_email = "alaa@gmail.com"
new_full_name = "Alaa Ahmed"
new_gender = "Female"
new_date_of_birth = "1990-01-01"  # YYYY-MM-DD
new_national_id = "12345678901234"

with app.app_context():
    user = User.query.filter_by(email=target_email).first()
    if user:
        user.full_name = new_full_name
        user.gender = new_gender
        user.date_of_birth = new_date_of_birth
        user.national_id = new_national_id
        db.session.commit()
        print(f"Updated user {user.email} with new profile info.")
    else:
        print(f"User with email {target_email} not found.")
