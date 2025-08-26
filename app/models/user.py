from datetime import datetime, UTC
from ..extensions import db


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('lt_role.role_id'))
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    # Relationships
    role = db.relationship('LtRole', backref='users')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role_id': self.role_id,
            'role': self.role.to_dict() if self.role else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }