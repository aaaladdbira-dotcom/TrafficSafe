from extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    gender = db.Column(db.String(16), nullable=True)  # Made nullable for social login
    date_of_birth = db.Column(db.Date, nullable=True)  # Made nullable for social login
    # Age is computed property, not stored
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    avatar_url = db.Column(db.String(256), nullable=True)
    dark_mode = db.Column(db.Boolean, default=False)
    national_id = db.Column(db.String(32), unique=True, nullable=False)
    user_type = db.Column(db.String(32), nullable=False)  # police, media, citizen
    work_place = db.Column(db.String(120), nullable=True)
    badge_number = db.Column(db.String(64), nullable=True)
    journalist_id = db.Column(db.String(64), nullable=True)
    oauth_provider = db.Column(db.String(32), nullable=True)  # google, facebook, apple

    @property
    def age(self):
        from datetime import date
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
