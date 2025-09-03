from datetime import datetime
from sqlalchemy import CheckConstraint
from app.extensions import db

class DtEmailCampaign(db.Model):
    __tablename__ = "dt_email_campaign"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    template = db.Column(db.Text, nullable=False)
    campaign_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='draft', nullable=False)
    target_segment = db.Column(db.String(50), nullable=True)
    product_filter = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    email_sends = db.relationship('DtEmailSend', backref='campaign', lazy='dynamic')

    __table_args__ = (
        CheckConstraint("campaign_type in ('loyalty', 'promotion', 'winback', 'event')", name="ck_campaign_type"),
        CheckConstraint("status in ('draft', 'scheduled', 'sent', 'completed')", name="ck_campaign_status"),
        CheckConstraint("target_segment in ('loyal', 'high_value', 'frequent', 'at_risk', 'product_specific')", name="ck_target_segment"),
    )


class DtEmailSend(db.Model):
    __tablename__ = "dt_email_send"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('dt_email_campaign.id'), nullable=False, index=True)
    customer_id = db.Column(db.String(100), db.ForeignKey('dt_customer.customer_id'), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    opened_at = db.Column(db.DateTime, nullable=True)
    clicked_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("status in ('pending', 'sent', 'delivered', 'bounced', 'opened', 'clicked')", name="ck_send_status"),
    )