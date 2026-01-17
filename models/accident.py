from extensions import db
from datetime import datetime

class Accident(db.Model):
    __tablename__ = "accidents"

    id = db.Column(db.Integer, primary_key=True)

    # Core info
    occurred_at = db.Column(db.DateTime, nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, index=True)
    cause = db.Column(db.String(100), nullable=True, index=True)

    # Location (simple but effective)
    location = db.Column(db.String(200), nullable=True)
    governorate = db.Column(db.String(200), nullable=True, index=True)
    delegation = db.Column(db.String(200), nullable=True, index=True)

    # Metadata
    source = db.Column(db.String(50), nullable=False, default="import")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Link to import batch when created via CSV import
    batch_id = db.Column(db.Integer, db.ForeignKey('import_batches.id'), nullable=True, index=True)

    def __repr__(self):
        return f"<Accident {self.id} | {self.severity} | {self.location}>"
