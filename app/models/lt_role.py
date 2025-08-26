from datetime import datetime, UTC
from ..extensions import db


class LtRole(db.Model):
    __tablename__ = 'lt_role'

    role_id = db.Column(db.Integer, primary_key=True)
    role_code = db.Column(db.String(50), unique=True, nullable=False)
    role_name = db.Column(db.String(100), nullable=False)
    role_description = db.Column(db.Text)
    role_permissions = db.Column(db.Text)
    role_is_active = db.Column(db.Boolean, default=True)
    role_created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    def to_dict(self):
        return {
            'role_id': self.role_id,
            'role_code': self.role_code,
            'role_name': self.role_name,
            'role_description': self.role_description,
            'role_permissions': self.role_permissions,
            'role_is_active': self.role_is_active,
            'role_created_at': self.role_created_at.isoformat() if self.role_created_at else None
        }