from datetime import datetime, UTC
from ..extensions import db


class LtCategoryCtgry(db.Model):
    __tablename__ = 'lt_category_ctgry'

    ctgry_id = db.Column(db.Integer, primary_key=True)
    ctgry_code = db.Column(db.String(50), unique=True, nullable=False)
    ctgry_name = db.Column(db.String(100), nullable=False)
    ctgry_description = db.Column(db.Text)
    ctgry_is_active = db.Column(db.Boolean, default=True)
    ctgry_created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    def to_dict(self):
        return {
            'ctgry_id': self.ctgry_id,
            'ctgry_code': self.ctgry_code,
            'ctgry_name': self.ctgry_name,
            'ctgry_description': self.ctgry_description,
            'ctgry_is_active': self.ctgry_is_active,
            'ctgry_created_at': self.ctgry_created_at.isoformat() if self.ctgry_created_at else None
        }