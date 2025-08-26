from datetime import datetime, UTC
from ..extensions import db


class DtTask(db.Model):
    __tablename__ = 'dt_task'

    task_id = db.Column(db.Integer, primary_key=True)
    user_story_id = db.Column(db.Integer, db.ForeignKey('dt_user_story.user_story_id'), nullable=False)
    task_title = db.Column(db.String(200), nullable=False)
    task_description = db.Column(db.Text)
    task_assignee_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # CHANGED
    task_priority_id = db.Column(db.Integer, db.ForeignKey('lt_priority.priority_id'))
    task_status_id = db.Column(db.Integer, db.ForeignKey('lt_general_status.status_id'))
    task_estimated_hours = db.Column(db.Float, default=0)
    task_labels = db.Column(db.String(500))
    task_due_date = db.Column(db.DateTime)
    notion_page_id = db.Column(db.String(100), nullable=True)
    notion_synced_at = db.Column(db.DateTime)
    notion_sync_status = db.Column(db.Enum('pending', 'synced', 'failed', 'skip', name='task_notion_sync_status_enum'), default='pending')
    task_created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    task_updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    # Relationships
    assignee = db.relationship('User', backref='assigned_tasks')
    priority = db.relationship('LtPriority', backref='tasks')
    status = db.relationship('LtGeneralStatus', backref='tasks')

    def __repr__(self):
        return f'<DtTask {self.task_id}: {self.task_title}>'

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'user_story_id': self.user_story_id,
            'task_title': self.task_title,
            'task_description': self.task_description,
            'task_assignee_user_id': self.task_assignee_user_id,
            'task_priority_id': self.task_priority_id,
            'task_status_id': self.task_status_id,
            'task_estimated_hours': self.task_estimated_hours,
            'task_labels': self.task_labels.split(',') if self.task_labels else [],
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'priority': self.priority.to_dict() if self.priority else None,
            'status': self.status.to_dict() if self.status else None,
            'notion_page_id': self.notion_page_id,
            'notion_synced_at': self.notion_synced_at.isoformat() if self.notion_synced_at else None,
            'notion_sync_status': self.notion_sync_status,
            'task_due_date': self.task_due_date.isoformat() if self.task_due_date else None,
            'task_created_at': self.task_created_at.isoformat() if self.task_created_at else None,
            'task_updated_at': self.task_updated_at.isoformat() if self.task_updated_at else None
        }