from datetime import datetime, UTC
from ..extensions import db


class DtGenerationLog(db.Model):
    __tablename__ = 'dt_generation_log'

    generation_log_id = db.Column(db.Integer, primary_key=True)
    user_story_id = db.Column(db.Integer, db.ForeignKey('dt_user_story.user_story_id'), nullable=False)
    generation_log_type_id = db.Column(db.Integer, db.ForeignKey('lt_category_ctgry.ctgry_id'))
    generation_log_status_id = db.Column(db.Integer, db.ForeignKey('lt_general_status.status_id'))
    generation_log_items_generated = db.Column(db.Integer, default=0)
    generation_log_error_message = db.Column(db.Text)
    generation_log_processing_time = db.Column(db.Float)
    generation_log_created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    # Relationships
    log_type = db.relationship('LtCategoryCtgry', backref='generation_logs')
    log_status = db.relationship('LtGeneralStatus', backref='generation_logs')

    def __repr__(self):
        return f'<DtGenerationLog {self.generation_log_id}: {self.log_type.ctgry_code if self.log_type else "Unknown"} for UserStory {self.user_story_id}>'

    def to_dict(self):
        return {
            'generation_log_id': self.generation_log_id,
            'user_story_id': self.user_story_id,
            'generation_log_type_id': self.generation_log_type_id,
            'generation_log_status_id': self.generation_log_status_id,
            'generation_log_items_generated': self.generation_log_items_generated,
            'generation_log_error_message': self.generation_log_error_message,
            'generation_log_processing_time': self.generation_log_processing_time,
            'log_type': self.log_type.to_dict() if self.log_type else None,
            'log_status': self.log_status.to_dict() if self.log_status else None,
            'generation_log_created_at': self.generation_log_created_at.isoformat() if self.generation_log_created_at else None
        }