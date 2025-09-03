# app/services/email_service.py

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import and_, func
from flask import current_app
from flask_mail import Mail, Message
from app.extensions import db
from app.models.dt_customer import DtCustomer
from app.models.dt_customer_purchase import DtCustomerPurchase
from app.models.dt_email_campaign import DtEmailCampaign, DtEmailSend
from app.services.customer_service import get_customer_segments

class EmailMarketingService:
    """
    Email marketing service for customer engagement campaigns
    """
    
    def __init__(self):
        self.mail = None
    
    def init_mail(self, app):
        """Initialize Flask-Mail with app"""
        self.mail = Mail(app)
    
    def _get_mail_instance(self):
        """Get Flask-Mail instance from current app context"""
        if self.mail is None:
            try:
                from flask import current_app
                from flask_mail import Mail
                self.mail = current_app.extensions.get('mail')
                if self.mail is None:
                    # If not found in extensions, try to create one
                    self.mail = Mail(current_app)
            except:
                pass
        return self.mail
    
    def send_email(self, to_email: str, subject: str, body: str, sender_name: str = None) -> bool:
        """Send email using Flask-Mail and Gmail SMTP"""
        try:
            sender_email = os.getenv('SENDER_EMAIL')
            sender_name = sender_name or os.getenv('SENDER_NAME', 'MVP2 System')
            sender = f"{sender_name} <{sender_email}>"
            
            msg = Message(
                subject=subject,
                sender=sender,
                recipients=[to_email],
                html=body
            )
            
            mail_instance = self._get_mail_instance()
            if mail_instance:
                mail_instance.send(msg)
                return True
            else:
                print(f"Email would be sent to {to_email}: {subject}")
                return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def create_loyalty_campaign(self, campaign_data: Dict[str, Any]) -> DtEmailCampaign:
        """
        Create a loyalty rewards campaign for repeat customers
        """
        min_orders = campaign_data.get("min_orders", 5)
        min_spent = campaign_data.get("min_spent", 1000)
        discount_percent = campaign_data.get("discount_percent", 20)
        
        # Generate email template
        template = self._generate_loyalty_template(discount_percent, campaign_data.get("template_vars", {}))
        
        campaign = DtEmailCampaign(
            name=campaign_data["name"],
            subject=campaign_data["subject"],
            template=template,
            campaign_type="loyalty",
            target_segment="loyal",
            status="draft"
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        # Get target customers
        loyal_customers = self._get_loyal_customers(min_orders, min_spent)
        self._create_email_sends(campaign.id, loyal_customers)
        
        return campaign
    
    def create_product_promotion_campaign(self, campaign_data: Dict[str, Any]) -> DtEmailCampaign:
        """
        Create a product promotion campaign for specific products
        """
        product_filter = campaign_data.get("product_filter")
        discount_percent = campaign_data.get("discount_percent", 10)
        target_customers = campaign_data.get("target_customers", "previous_buyers")
        
        template = self._generate_product_promotion_template(
            product_filter, discount_percent, campaign_data.get("template_vars", {})
        )
        
        campaign = DtEmailCampaign(
            name=campaign_data["name"],
            subject=campaign_data["subject"],
            template=template,
            campaign_type="promotion",
            target_segment="product_specific",
            product_filter=product_filter,
            status="draft"
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        # Get customers who bought this product type before
        if target_customers == "previous_buyers":
            customers = self._get_product_buyers(product_filter)
        else:
            customers = self._get_all_customers_with_email()
            
        self._create_email_sends(campaign.id, customers)
        
        return campaign
    
    def create_winback_campaign(self, campaign_data: Dict[str, Any]) -> DtEmailCampaign:
        """
        Create a win-back campaign for inactive customers
        """
        inactive_days = campaign_data.get("inactive_days", 90)
        discount_percent = campaign_data.get("discount_percent", 25)
        
        template = self._generate_winback_template(discount_percent, campaign_data.get("template_vars", {}))
        
        campaign = DtEmailCampaign(
            name=campaign_data["name"],
            subject=campaign_data["subject"],
            template=template,
            campaign_type="winback",
            target_segment="at_risk",
            status="draft"
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        # Get inactive customers
        inactive_customers = self._get_inactive_customers(inactive_days)
        self._create_email_sends(campaign.id, inactive_customers)
        
        return campaign
    
    def send_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """
        Send email campaign to all targeted customers
        """
        campaign = DtEmailCampaign.query.get_or_404(campaign_id)
        
        if campaign.status != "draft":
            return {"error": "Campaign already sent or not in draft status"}
        
        # Get all pending email sends for this campaign
        email_sends = DtEmailSend.query.filter_by(
            campaign_id=campaign_id, 
            status="pending"
        ).all()
        
        sent_count = 0
        failed_count = 0
        
        for email_send in email_sends:
            try:
                # In a real implementation, you'd call your email service API here
                success = self._send_email(email_send)
                
                if success:
                    email_send.status = "sent"
                    email_send.sent_at = datetime.utcnow()
                    sent_count += 1
                else:
                    email_send.status = "failed"
                    email_send.error_message = "Failed to send email"
                    failed_count += 1
                    
            except Exception as e:
                email_send.status = "failed"
                email_send.error_message = str(e)
                failed_count += 1
        
        # Update campaign status
        campaign.status = "sent"
        campaign.sent_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            "campaign_id": campaign_id,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_recipients": len(email_sends)
        }
    
    def get_campaign_stats(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get analytics for a specific campaign
        """
        campaign = DtEmailCampaign.query.get_or_404(campaign_id)
        
        # Get email send statistics
        stats = db.session.query(
            DtEmailSend.status,
            func.count(DtEmailSend.id).label('count')
        ).filter_by(campaign_id=campaign_id).group_by(DtEmailSend.status).all()
        
        status_counts = {status: count for status, count in stats}
        
        total_sent = status_counts.get("sent", 0)
        total_delivered = status_counts.get("delivered", 0)
        total_opened = status_counts.get("opened", 0)
        total_clicked = status_counts.get("clicked", 0)
        total_failed = status_counts.get("failed", 0)
        
        # Calculate rates
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0
        click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0
        
        return {
            "campaign": {
                "id": campaign.id,
                "name": campaign.name,
                "subject": campaign.subject,
                "campaign_type": campaign.campaign_type,
                "status": campaign.status,
                "created_at": campaign.created_at.isoformat(),
                "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None
            },
            "stats": {
                "total_recipients": sum(status_counts.values()),
                "sent": total_sent,
                "delivered": total_delivered,
                "opened": total_opened,
                "clicked": total_clicked,
                "failed": total_failed,
                "delivery_rate": round(delivery_rate, 2),
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2)
            }
        }
    
    def send_custom_email(self, subject: str, body: str, segment: str = "all", 
                         product_filter: Optional[str] = None, sender_name: str = "The Team",
                         customer_id: Optional[str] = None, customer_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Send custom email with custom subject and body to customers
        """
        # Get target customers based on segment
        if segment == "all":
            customers = self._get_all_customers_with_email()
        elif segment == "loyal":
            customers = self._get_loyal_customers(min_orders=5, min_spent=1000)
        elif segment == "high_value":
            # Get customers with above average spend
            avg_spent = db.session.query(func.avg(DtCustomer.total_spent)).scalar() or 0
            customers = DtCustomer.query.filter(
                and_(
                    DtCustomer.total_spent >= avg_spent * 1.5,
                    DtCustomer.email.isnot(None),
                    DtCustomer.email != ""
                )
            ).all()
        elif segment == "frequent":
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            customers = DtCustomer.query.filter(
                and_(
                    DtCustomer.last_purchase_date >= thirty_days_ago,
                    DtCustomer.email.isnot(None),
                    DtCustomer.email != ""
                )
            ).all()
        elif segment == "at_risk":
            ninety_days_ago = datetime.now().date() - timedelta(days=90)
            customers = DtCustomer.query.filter(
                and_(
                    DtCustomer.last_purchase_date < ninety_days_ago,
                    DtCustomer.total_orders > 0,
                    DtCustomer.email.isnot(None),
                    DtCustomer.email != ""
                )
            ).all()
        elif segment == "individual":
            if not customer_id and not customer_email:
                return {"error": "customer_id or customer_email is required for individual segment"}
            
            if customer_id:
                customer = DtCustomer.query.filter_by(customer_id=customer_id).first()
            elif customer_email:
                customer = DtCustomer.query.filter_by(email=customer_email).first()
            
            if not customer:
                return {"error": "Customer not found"}
            
            if not customer.email:
                return {"error": "Customer has no email address"}
            
            customers = [customer]
        elif product_filter:
            customers = self._get_product_buyers(product_filter)
        else:
            return {"error": "Invalid segment type"}
        
        if not customers:
            return {"error": f"No customers found for segment: {segment}"}
        
        # Create a temporary campaign for tracking
        campaign = DtEmailCampaign(
            name=f"Custom Email - {segment.title()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            subject=subject,
            template=self._generate_custom_template(body, sender_name),
            campaign_type="event",  # Custom emails are event type
            target_segment=segment if segment not in ["all", "individual"] else None,
            product_filter=product_filter,
            status="draft"
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        # Create email sends
        self._create_email_sends(campaign.id, customers)
        
        # Send immediately
        result = self.send_campaign(campaign.id)
        
        return {
            "campaign_id": campaign.id,
            "campaign_name": campaign.name,
            "subject": subject,
            "segment": segment,
            "target_customers": len(customers),
            "send_result": result
        }

    def get_all_campaigns(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Get all email campaigns with pagination
        """
        campaigns = DtEmailCampaign.query.order_by(
            DtEmailCampaign.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        campaign_list = []
        for campaign in campaigns.items:
            # Get quick stats
            total_recipients = DtEmailSend.query.filter_by(campaign_id=campaign.id).count()
            sent_count = DtEmailSend.query.filter_by(campaign_id=campaign.id, status="sent").count()
            
            campaign_data = {
                "id": campaign.id,
                "name": campaign.name,
                "subject": campaign.subject,
                "campaign_type": campaign.campaign_type,
                "status": campaign.status,
                "target_segment": campaign.target_segment,
                "created_at": campaign.created_at.isoformat(),
                "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
                "total_recipients": total_recipients,
                "sent_count": sent_count
            }
            campaign_list.append(campaign_data)
        
        return {
            "campaigns": campaign_list,
            "pagination": {
                "page": campaigns.page,
                "pages": campaigns.pages,
                "per_page": campaigns.per_page,
                "total": campaigns.total,
            }
        }
    
    # Private helper methods
    
    def _get_loyal_customers(self, min_orders: int, min_spent: float) -> List[DtCustomer]:
        """Get customers meeting loyalty criteria"""
        return DtCustomer.query.filter(
            and_(
                DtCustomer.total_orders >= min_orders,
                DtCustomer.total_spent >= min_spent,
                DtCustomer.email.isnot(None),
                DtCustomer.email != ""
            )
        ).all()
    
    def _get_inactive_customers(self, days: int) -> List[DtCustomer]:
        """Get customers inactive for specified days"""
        cutoff_date = datetime.now().date() - timedelta(days=days)
        return DtCustomer.query.filter(
            and_(
                DtCustomer.last_purchase_date < cutoff_date,
                DtCustomer.total_orders > 0,
                DtCustomer.email.isnot(None),
                DtCustomer.email != ""
            )
        ).all()
    
    def _get_product_buyers(self, product_filter: str) -> List[DtCustomer]:
        """Get customers who bought specific products"""
        customer_ids = db.session.query(DtCustomerPurchase.customer_id).filter(
            DtCustomerPurchase.item_name.like(f"%{product_filter}%")
        ).distinct().subquery()
        
        return DtCustomer.query.filter(
            and_(
                DtCustomer.customer_id.in_(customer_ids),
                DtCustomer.email.isnot(None),
                DtCustomer.email != ""
            )
        ).all()
    
    def _get_all_customers_with_email(self) -> List[DtCustomer]:
        """Get all customers with valid email addresses"""
        return DtCustomer.query.filter(
            and_(
                DtCustomer.email.isnot(None),
                DtCustomer.email != ""
            )
        ).all()
    
    def _create_email_sends(self, campaign_id: int, customers: List[DtCustomer]):
        """Create email send records for campaign"""
        for customer in customers:
            email_send = DtEmailSend(
                campaign_id=campaign_id,
                customer_id=customer.customer_id,
                email=customer.email,
                status="pending"
            )
            db.session.add(email_send)
        db.session.commit()
    
    def _send_email(self, email_send: DtEmailSend) -> bool:
        """
        Send individual email using Flask-Mail
        """
        try:
            # Get the campaign
            campaign = DtEmailCampaign.query.get(email_send.campaign_id)
            if not campaign:
                return False
            
            # Get customer for personalization
            customer = DtCustomer.query.filter_by(customer_id=email_send.customer_id).first()
            customer_name = customer.name if customer else "Valued Customer"
            
            # Personalize the template
            personalized_body = campaign.template.replace("{{ customer_name }}", customer_name)
            
            # Send the actual email
            return self.send_email(
                to_email=email_send.email,
                subject=campaign.subject,
                body=personalized_body,
                sender_name=None  # Uses default from env
            )
            
        except Exception as e:
            print(f"Failed to send email to {email_send.email}: {e}")
            return False
    
    def _generate_loyalty_template(self, discount_percent: int, template_vars: Dict) -> str:
        """Generate loyalty email template"""
        promo_code = template_vars.get("promo_code", f"LOYAL{discount_percent}")
        expires = template_vars.get("expires", "2024-12-31")
        
        return f"""
Dear {{{{ customer_name }}}},

Thank you for being a valued customer! As a token of our appreciation for your loyalty, we're offering you an exclusive {discount_percent}% discount on your next purchase.

Use promo code: {promo_code}
Valid until: {expires}

Shop now and save on all your favorite items!

Best regards,
The Team
"""
    
    def _generate_product_promotion_template(self, product: str, discount_percent: int, template_vars: Dict) -> str:
        """Generate product promotion email template"""
        product_name = template_vars.get("product_name", product)
        special_price = template_vars.get("special_price", f"{discount_percent}% off")
        
        return f"""
Dear {{{{ customer_name }}}},

Great news! The {product_name} you've been interested in is now available with a special discount.

🎉 {special_price} - Limited Time Only!

Based on your previous purchases, we think you'll love this new addition to our {product} collection.

Shop now before this offer expires!

Best regards,
The Team
"""
    
    def _generate_winback_template(self, discount_percent: int, template_vars: Dict) -> str:
        """Generate win-back email template"""
        promo_code = template_vars.get("promo_code", f"COMEBACK{discount_percent}")
        
        return f"""
Hi {{{{ customer_name }}}},

We miss you! It's been a while since your last visit, and we'd love to welcome you back with a special offer.

🎁 {discount_percent}% OFF your next order!
Use code: {promo_code}

Come back and see what's new - we've got some exciting products we think you'll love.

Welcome back!
The Team
"""
    
    def _generate_custom_template(self, body: str, sender_name: str) -> str:
        """Generate custom email template"""
        return f"""
Dear {{{{ customer_name }}}},

{body}

Best regards,
{sender_name}
"""


# Convenience function for easy access
def get_email_service() -> EmailMarketingService:
    """Get email marketing service instance"""
    return EmailMarketingService()