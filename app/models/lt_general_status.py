from datetime import datetime, UTC
from ..extensions import db


class LtGeneralStatus(db.Model):
    __tablename__ = 'lt_general_status'

    status_id = db.Column(db.Integer, primary_key=True)
    status_code = db.Column(db.String(50), unique=True, nullable=False)
    status_name = db.Column(db.String(100), nullable=False)
    status_description = db.Column(db.Text)
    status_category = db.Column(db.String(50))
    status_is_active = db.Column(db.Boolean, default=True)
    status_created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    def to_dict(self):
        return {
            'status_id': self.status_id,
            'status_code': self.status_code,
            'status_name': self.status_name,
            'status_description': self.status_description,
            'status_category': self.status_category,
            'status_is_active': self.status_is_active,
            'status_created_at': self.status_created_at.isoformat() if self.status_created_at else None
        }