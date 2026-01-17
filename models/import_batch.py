from extensions import db
from datetime import datetime


class ImportBatch(db.Model):
    __tablename__ = "import_batches"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=True)
    uploader_id = db.Column(db.String(64), nullable=True)
    uploader_role = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    imported_count = db.Column(db.Integer, default=0)
    skipped_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<ImportBatch {self.id} file={self.filename} imported={self.imported_count}>"