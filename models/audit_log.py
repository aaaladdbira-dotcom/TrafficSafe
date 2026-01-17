"""
Audit Log Model
===============
Tracks all data modifications with user info
"""

from extensions import db
from datetime import datetime


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    
    # Who made the change
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_email = db.Column(db.String(120), nullable=True)  # Stored separately for deleted users
    
    # What was changed
    action = db.Column(db.String(50), nullable=False)  # create, update, delete, login, export, etc.
    entity_type = db.Column(db.String(50), nullable=False)  # accident, user, report, etc.
    entity_id = db.Column(db.Integer, nullable=True)
    
    # Change details
    old_values = db.Column(db.Text, nullable=True)  # JSON string of old values
    new_values = db.Column(db.Text, nullable=True)  # JSON string of new values
    description = db.Column(db.String(500), nullable=True)
    
    # Context
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog {self.id} | {self.action} | {self.entity_type}>"

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ip_address': self.ip_address
        }
