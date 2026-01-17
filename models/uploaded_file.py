"""
File Upload Model
=================
Store metadata for uploaded files
"""

from extensions import db
from datetime import datetime


class UploadedFile(db.Model):
    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True)
    
    # File info
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_type = db.Column(db.String(50), nullable=False)  # image, document, etc.
    mime_type = db.Column(db.String(100), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    
    # Association
    entity_type = db.Column(db.String(50), nullable=True)  # accident_report, accident, etc.
    entity_id = db.Column(db.Integer, nullable=True)
    
    # Ownership
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UploadedFile {self.id} | {self.original_filename}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
