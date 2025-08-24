from datetime import datetime, UTC
from ..extensions import db

class DtCompanyCom(db.Model):
    __tablename__ = 'dt_company_com'
    
    com_id = db.Column(db.Integer, primary_key=True)
    com_name = db.Column(db.String(100), nullable=False)
    com_code = db.Column(db.String(20), unique=True, nullable=False)
    com_description = db.Column(db.Text)
    com_website = db.Column(db.String(255))
    com_is_active = db.Column(db.Boolean, default=True)
    com_created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    com_updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    user_details = db.relationship('DtUserDetail', backref='company', lazy=True, cascade='all, delete-orphan')
    notion_accounts = db.relationship('DtNotionAccount', backref='company', lazy=True, cascade='all, delete-orphan')
    user_stories = db.relationship('DtUserStory', backref='company', lazy=True)
    
    def __repr__(self):
        return f'<DtCompanyCom {self.com_id}: {self.com_name}>'
    
    def to_dict(self):
        return {
            'com_id': self.com_id,
            'com_name': self.com_name,
            'com_code': self.com_code,
            'com_description': self.com_description,
            'com_website': self.com_website,
            'com_is_active': self.com_is_active,
            'com_created_at': self.com_created_at.isoformat() if self.com_created_at else None,
            'com_updated_at': self.com_updated_at.isoformat() if self.com_updated_at else None
        }