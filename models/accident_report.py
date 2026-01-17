from extensions import db
from datetime import datetime

class AccidentReport(db.Model):
    __tablename__ = "accident_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(256), nullable=False)
    delegation = db.Column(db.String(128), nullable=False)
    severity = db.Column(db.String(32), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="PENDING")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accident_id = db.Column(db.Integer, db.ForeignKey("accidents.id"), nullable=True)
    rejection_reason = db.Column(db.String(256), nullable=True)

    user = db.relationship("User", backref="accident_reports")
    accident = db.relationship("Accident", backref="report", uselist=False)
