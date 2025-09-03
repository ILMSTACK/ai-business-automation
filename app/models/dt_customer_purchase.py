from datetime import datetime
from app.extensions import db

class DtCustomerPurchase(db.Model):
    __tablename__ = "dt_customer_purchase"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(100), db.ForeignKey('dt_customer.customer_id'), nullable=False, index=True)
    invoice_id = db.Column(db.String(100), nullable=False, index=True)
    invoice_date = db.Column(db.Date, nullable=False, index=True)
    item_id = db.Column(db.String(100), nullable=False, index=True)
    item_name = db.Column(db.String(255), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    revenue = db.Column(db.Numeric(10, 2), nullable=False)
    csv_upload_id = db.Column(db.Integer, db.ForeignKey('csv_uploads.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    csv_upload = db.relationship('CsvUpload', backref='customer_purchases')