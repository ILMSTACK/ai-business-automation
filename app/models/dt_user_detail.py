from datetime import datetime, UTC
from ..extensions import db

class DtUserDetail(db.Model):
    __tablename__ = 'dt_user_detail'
    
    user_detail_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    com_id = db.Column(db.Integer, db.ForeignKey('dt_company_com.com_id'), nullable=False)
    user_role = db.Column(db.String(50), default='member')
    user_permissions = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    user = db.relationship('User', backref='user_details')
    
    def __repr__(self):
        return f'<DtUserDetail {self.user_detail_id}: User {self.user_id} in Company {self.com_id}>'
    
    def to_dict(self):
        return {
            'user_detail_id': self.user_detail_id,
            'user_id': self.user_id,
            'com_id': self.com_id,
            'user_role': self.user_role,
            'user_permissions': self.user_permissions,
            'is_active': self.is_active,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }