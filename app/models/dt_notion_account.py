from datetime import datetime, UTC
from ..extensions import db

class DtNotionAccount(db.Model):
    __tablename__ = 'dt_notion_account'
    
    notion_id = db.Column(db.Integer, primary_key=True)
    com_id = db.Column(db.Integer, db.ForeignKey('dt_company_com.com_id'), nullable=False)
    notion_token = db.Column(db.Text, nullable=False)  # Will be encoded
    notion_parent_page_id = db.Column(db.String(100), nullable=False)
    tasks_database_id = db.Column(db.String(100))
    testcases_database_id = db.Column(db.String(100))
    workspace_name = db.Column(db.String(100))
    integration_name = db.Column(db.String(100), default='AI Business Automation')
    is_active = db.Column(db.Boolean, default=True)
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.Enum('active', 'error', 'disabled', name='sync_status_enum'), default='active')
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    def __repr__(self):
        return f'<DtNotionAccount {self.notion_id}: Company {self.com_id}>'
    
    def to_dict(self):
        return {
            'notion_id': self.notion_id,
            'com_id': self.com_id,
            'workspace_name': self.workspace_name,
            'integration_name': self.integration_name,
            'is_active': self.is_active,
            'sync_status': self.sync_status,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'tasks_database_id': self.tasks_database_id,
            'testcases_database_id': self.testcases_database_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }