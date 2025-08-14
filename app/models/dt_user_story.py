from datetime import datetime, UTC
from ..extensions import db

class DtUserStory(db.Model):
    __tablename__ = 'dt_user_story'
    
    user_story_id = db.Column(db.Integer, primary_key=True)
    user_story_title = db.Column(db.String(200), nullable=False)
    user_story_content = db.Column(db.Text, nullable=False)
    user_story_created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    user_story_updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    # Explicit relationships with updated class names
    testcases = db.relationship('DtTestCase', 
                               primaryjoin='DtUserStory.user_story_id == DtTestCase.user_story_id',
                               backref='user_story', 
                               lazy=True, 
                               cascade='all, delete-orphan')
    
    tasks = db.relationship('DtTask', 
                           primaryjoin='DtUserStory.user_story_id == DtTask.user_story_id',
                           backref='user_story', 
                           lazy=True, 
                           cascade='all, delete-orphan')
    
    generation_logs = db.relationship('DtGenerationLog', 
                                     primaryjoin='DtUserStory.user_story_id == DtGenerationLog.user_story_id',
                                     backref='user_story', 
                                     lazy=True, 
                                     cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DtUserStory {self.user_story_id}: {self.user_story_title}>'

    def to_dict(self):
        return {
            'user_story_id': self.user_story_id,
            'user_story_title': self.user_story_title,
            'user_story_content': self.user_story_content,
            'user_story_created_at': self.user_story_created_at.isoformat() if self.user_story_created_at else None,
            'user_story_updated_at': self.user_story_updated_at.isoformat() if self.user_story_updated_at else None
        }