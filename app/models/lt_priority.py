from datetime import datetime, UTC
from ..extensions import db


class LtPriority(db.Model):
    __tablename__ = 'lt_priority'

    priority_id = db.Column(db.Integer, primary_key=True)
    priority_code = db.Column(db.String(50), unique=True, nullable=False)
    priority_name = db.Column(db.String(100), nullable=False)
    priority_level = db.Column(db.Integer)
    priority_color = db.Column(db.String(7))
    priority_is_active = db.Column(db.Boolean, default=True)
    priority_created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    def to_dict(self):
        return {
            'priority_id': self.priority_id,
            'priority_code': self.priority_code,
            'priority_name': self.priority_name,
            'priority_level': self.priority_level,
            'priority_color': self.priority_color,
            'priority_is_active': self.priority_is_active,
            'priority_created_at': self.priority_created_at.isoformat() if self.priority_created_at else None
        }