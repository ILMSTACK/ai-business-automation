from datetime import datetime
from app.extensions import db

class DtCustomer(db.Model):
    __tablename__ = "dt_customer"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    first_purchase_date = db.Column(db.Date, nullable=True)
    last_purchase_date = db.Column(db.Date, nullable=True)
    total_orders = db.Column(db.Integer, default=0, nullable=False)
    total_spent = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    purchases = db.relationship('DtCustomerPurchase', backref='customer', lazy='dynamic')
    email_sends = db.relationship('DtEmailSend', backref='customer', lazy='dynamic')