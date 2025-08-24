from datetime import datetime
from sqlalchemy import CheckConstraint
from app.extensions import db

class CsvUpload(db.Model):
    __tablename__ = "csv_uploads"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)  # isi jika ada auth
    csv_type = db.Column(db.String(20), nullable=False)  # 'sales' | 'inventory'
    csv_path = db.Column(db.Text, nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    row_count = db.Column(db.Integer, nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)
    content_sha256 = db.Column(db.String(64), nullable=True, index=True)
    detected_columns = db.Column(db.Text, nullable=True)  # JSON string of header
    status = db.Column(db.String(20), nullable=False, default="uploaded")  # uploaded|validated|invalid|processed|failed
    error_msg = db.Column(db.Text, nullable=True)

    batch_id = db.Column(db.String(64), nullable=True, index=True)  # optional pairing sales/inventory
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    validated_at = db.Column(db.DateTime, nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("csv_type in ('sales','inventory')", name="ck_csv_type"),
    )
