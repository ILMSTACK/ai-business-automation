# app/services/customer_service.py

import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.extensions import db
from app.models.dt_customer import DtCustomer
from app.models.dt_customer_purchase import DtCustomerPurchase
from typing import Optional, List, Dict, Any

def get_all_customers(page: int = 1, per_page: int = 50) -> Dict[str, Any]:
    """
    Get all customers with pagination and basic stats
    """
    customers = DtCustomer.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    customer_list = []
    for customer in customers.items:
        customer_data = {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "address": customer.address,
            "first_purchase_date": customer.first_purchase_date.isoformat() if customer.first_purchase_date else None,
            "last_purchase_date": customer.last_purchase_date.isoformat() if customer.last_purchase_date else None,
            "total_orders": customer.total_orders,
            "total_spent": float(customer.total_spent),
            "created_at": customer.created_at.isoformat(),
        }
        customer_list.append(customer_data)
    
    return {
        "customers": customer_list,
        "pagination": {
            "page": customers.page,
            "pages": customers.pages,
            "per_page": customers.per_page,
            "total": customers.total,
        }
    }

def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
    """
    Get individual customer profile with detailed stats
    """
    customer = DtCustomer.query.filter_by(customer_id=customer_id).first()
    if not customer:
        return None
    
    # Calculate additional metrics
    recent_purchases = DtCustomerPurchase.query.filter_by(
        customer_id=customer_id
    ).order_by(DtCustomerPurchase.invoice_date.desc()).limit(5).all()
    
    # Average order value
    aov = float(customer.total_spent / customer.total_orders) if customer.total_orders > 0 else 0.0
    
    # Days since last purchase
    days_since_last = None
    if customer.last_purchase_date:
        days_since_last = (datetime.now().date() - customer.last_purchase_date).days
    
    return {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "first_purchase_date": customer.first_purchase_date.isoformat() if customer.first_purchase_date else None,
        "last_purchase_date": customer.last_purchase_date.isoformat() if customer.last_purchase_date else None,
        "total_orders": customer.total_orders,
        "total_spent": float(customer.total_spent),
        "average_order_value": aov,
        "days_since_last_purchase": days_since_last,
        "created_at": customer.created_at.isoformat(),
        "recent_purchases": [
            {
                "invoice_id": p.invoice_id,
                "invoice_date": p.invoice_date.isoformat(),
                "item_name": p.item_name,
                "qty": p.qty,
                "revenue": float(p.revenue)
            } for p in recent_purchases
        ]
    }

def get_customer_purchases(customer_id: str, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """
    Get customer purchase history with pagination
    """
    purchases = DtCustomerPurchase.query.filter_by(
        customer_id=customer_id
    ).order_by(DtCustomerPurchase.invoice_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    purchase_list = []
    for purchase in purchases.items:
        purchase_data = {
            "id": purchase.id,
            "invoice_id": purchase.invoice_id,
            "invoice_date": purchase.invoice_date.isoformat(),
            "item_id": purchase.item_id,
            "item_name": purchase.item_name,
            "qty": purchase.qty,
            "unit_price": float(purchase.unit_price),
            "revenue": float(purchase.revenue),
            "created_at": purchase.created_at.isoformat(),
        }
        purchase_list.append(purchase_data)
    
    return {
        "purchases": purchase_list,
        "pagination": {
            "page": purchases.page,
            "pages": purchases.pages,
            "per_page": purchases.per_page,
            "total": purchases.total,
        }
    }

def get_customer_segments(segment_type: str) -> Dict[str, Any]:
    """
    Get customers by segment type
    """
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    ninety_days_ago = datetime.now().date() - timedelta(days=90)
    
    query = DtCustomer.query
    criteria = ""
    
    if segment_type == "loyal":
        # Customers with 5+ orders and $1000+ spent
        query = query.filter(
            and_(DtCustomer.total_orders >= 5, DtCustomer.total_spent >= 1000)
        )
        criteria = "orders >= 5 AND total_spent >= 1000"
        
    elif segment_type == "high_value":
        # Customers with above average order value (assuming $200+)
        avg_spent = db.session.query(func.avg(DtCustomer.total_spent)).scalar() or 0
        query = query.filter(DtCustomer.total_spent >= avg_spent * 1.5)
        criteria = f"total_spent >= {avg_spent * 1.5:.2f} (1.5x average)"
        
    elif segment_type == "frequent":
        # Customers with recent purchases (within 30 days)
        query = query.filter(DtCustomer.last_purchase_date >= thirty_days_ago)
        criteria = "last_purchase_date >= 30 days ago"
        
    elif segment_type == "at_risk":
        # Customers who haven't purchased in 90+ days but have purchased before
        query = query.filter(
            and_(
                DtCustomer.last_purchase_date < ninety_days_ago,
                DtCustomer.total_orders > 0
            )
        )
        criteria = "last_purchase_date < 90 days ago AND total_orders > 0"
        
    else:
        return {"error": "Invalid segment type"}
    
    customers = query.all()
    
    customer_list = []
    for customer in customers:
        customer_data = {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "email": customer.email,
            "total_orders": customer.total_orders,
            "total_spent": float(customer.total_spent),
            "last_purchase": customer.last_purchase_date.isoformat() if customer.last_purchase_date else None,
        }
        customer_list.append(customer_data)
    
    return {
        "segment": segment_type,
        "criteria": criteria,
        "count": len(customer_list),
        "customers": customer_list
    }

def get_customers_for_upload(upload_id: int) -> Dict[str, Any]:
    """
    Get customer analysis for specific CSV upload
    """
    # Get purchases from this upload
    purchases = DtCustomerPurchase.query.filter_by(csv_upload_id=upload_id).all()
    
    if not purchases:
        return {
            "unique_customers": 0,
            "new_customers": 0,
            "repeat_customers": 0,
            "customers": []
        }
    
    # Get unique customer IDs from this upload
    customer_ids = list(set([p.customer_id for p in purchases]))
    
    # Get customer details
    customers = DtCustomer.query.filter(DtCustomer.customer_id.in_(customer_ids)).all()
    
    # Classify customers as new or repeat based on first purchase date
    upload_date = purchases[0].created_at.date()
    new_customers = 0
    repeat_customers = 0
    
    customer_list = []
    for customer in customers:
        is_new = customer.first_purchase_date == upload_date
        if is_new:
            new_customers += 1
        else:
            repeat_customers += 1
            
        # Calculate metrics for this upload only
        customer_purchases = [p for p in purchases if p.customer_id == customer.customer_id]
        upload_revenue = sum(float(p.revenue) for p in customer_purchases)
        upload_orders = len(set(p.invoice_id for p in customer_purchases))
        
        customer_data = {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "email": customer.email,
            "is_new_customer": is_new,
            "upload_revenue": upload_revenue,
            "upload_orders": upload_orders,
            "total_orders": customer.total_orders,
            "total_spent": float(customer.total_spent),
        }
        customer_list.append(customer_data)
    
    return {
        "unique_customers": len(customer_ids),
        "new_customers": new_customers,
        "repeat_customers": repeat_customers,
        "customers": customer_list
    }

def get_customer_metrics() -> Dict[str, Any]:
    """
    Get overall customer KPIs
    """
    total_customers = DtCustomer.query.count()
    
    # Recent customers (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_customers = DtCustomer.query.filter(
        DtCustomer.created_at >= thirty_days_ago
    ).count()
    
    # Active customers (purchased in last 90 days)
    ninety_days_ago = datetime.now().date() - timedelta(days=90)
    active_customers = DtCustomer.query.filter(
        DtCustomer.last_purchase_date >= ninety_days_ago
    ).count()
    
    # Average metrics
    avg_spent = db.session.query(func.avg(DtCustomer.total_spent)).scalar() or 0
    avg_orders = db.session.query(func.avg(DtCustomer.total_orders)).scalar() or 0
    
    # Churn rate (customers who haven't purchased in 90+ days)
    inactive_customers = total_customers - active_customers if total_customers > 0 else 0
    churn_rate = (inactive_customers / total_customers * 100) if total_customers > 0 else 0
    
    return {
        "total_customers": total_customers,
        "new_customers_30d": new_customers,
        "active_customers": active_customers,
        "churn_rate": round(churn_rate, 2),
        "average_spent": round(float(avg_spent), 2),
        "average_orders": round(float(avg_orders), 1),
    }