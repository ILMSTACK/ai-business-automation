from datetime import datetime, UTC
from ..extensions import db

class DtTestCase(db.Model):
    __tablename__ = 'dt_test_case'

    test_case_id = db.Column(db.Integer, primary_key=True)
    user_story_id = db.Column(db.Integer, db.ForeignKey('dt_user_story.user_story_id'), nullable=False)
    test_case_title = db.Column(db.String(200), nullable=False)
    test_case_description = db.Column(db.Text)
    test_case_steps = db.Column(db.JSON)
    test_case_expected_result = db.Column(db.Text)
    test_case_priority_id = db.Column(db.Integer, db.ForeignKey('lt_priority.priority_id'))
    test_case_type_id = db.Column(db.Integer, db.ForeignKey('lt_category_ctgry.ctgry_id'))
    test_case_status_id = db.Column(db.Integer, db.ForeignKey('lt_general_status.status_id'))
    test_case_created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    test_case_updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    priority = db.relationship('LtPriority', backref='test_cases')
    test_type = db.relationship('LtCategoryCtgry', backref='test_cases')
    status = db.relationship('LtGeneralStatus', backref='test_cases')

    def __repr__(self):
        return f'<DtTestCase {self.test_case_id}: {self.test_case_title}>'

    def to_dict(self):
        import json

        # Handle JSON field that might be bytes or string
        steps = self.test_case_steps
        if isinstance(steps, bytes):
            try:
                steps = json.loads(steps.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                steps = []
        elif isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except json.JSONDecodeError:
                steps = []
        elif steps is None:
            steps = []

        return {
            'test_case_id': self.test_case_id,
            'user_story_id': self.user_story_id,
            'test_case_title': self.test_case_title,
            'test_case_description': self.test_case_description,
            'test_case_steps': steps,
            'test_case_expected_result': self.test_case_expected_result,
            'test_case_priority_id': self.test_case_priority_id,
            'test_case_type_id': self.test_case_type_id,
            'test_case_status_id': self.test_case_status_id,
            'priority': self.priority.to_dict() if self.priority else None,
            'test_type': self.test_type.to_dict() if self.test_type else None,
            'status': self.status.to_dict() if self.status else None,
            'test_case_created_at': self.test_case_created_at.isoformat() if self.test_case_created_at else None,
            'test_case_updated_at': self.test_case_updated_at.isoformat() if self.test_case_updated_at else None
        }