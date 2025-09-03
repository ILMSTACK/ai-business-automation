# app/routes/email_routes.py - Email Marketing Routes (MVP2)

from flask import request
from flask_restx import Namespace, Resource
from app.services.email_service import get_email_service

# Initialize Namespace for Email Marketing operations
api = Namespace("email", description="Email marketing campaigns and analytics")

@api.route("/campaigns")
class EmailCampaigns(Resource):
    @api.doc("get_email_campaigns", params={
        "page": "Page number (default 1)",
        "per_page": "Items per page (default 20, max 50)"
    })
    def get(self):
        """Get all email campaigns with pagination"""
        page = request.args.get("page", default=1, type=int)
        per_page = min(request.args.get("per_page", default=20, type=int), 50)
        
        email_service = get_email_service()
        return email_service.get_all_campaigns(page=page, per_page=per_page)

@api.route("/campaigns/<int:campaign_id>/stats")
@api.param("campaign_id", "Campaign ID")
class EmailCampaignStats(Resource):
    @api.doc("get_campaign_stats")
    def get(self, campaign_id: int):
        """Get email campaign analytics and statistics"""
        email_service = get_email_service()
        return email_service.get_campaign_stats(campaign_id)

@api.route("/loyalty-promotion")
class EmailLoyaltyPromotion(Resource):
    @api.doc("create_loyalty_campaign")
    def post(self):
        """Create and optionally send loyalty rewards campaign"""
        data = request.get_json()
        if not data:
            return {"error": "JSON data required"}, 400
        
        required_fields = ["name", "subject"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return {"error": f"Missing required fields: {missing}"}, 400
        
        try:
            email_service = get_email_service()
            campaign = email_service.create_loyalty_campaign(data)
            
            result = {
                "ok": True,
                "campaign_id": campaign.id,
                "name": campaign.name,
                "subject": campaign.subject,
                "campaign_type": campaign.campaign_type,
                "status": campaign.status
            }
            
            # Auto-send if requested
            if data.get("auto_send", False):
                send_result = email_service.send_campaign(campaign.id)
                result["send_result"] = send_result
            
            return result, 201
            
        except Exception as e:
            return {"error": str(e)}, 400

@api.route("/product-promotion")
class EmailProductPromotion(Resource):
    @api.doc("create_product_promotion")
    def post(self):
        """Create product-specific promotion campaign"""
        data = request.get_json()
        if not data:
            return {"error": "JSON data required"}, 400
        
        required_fields = ["name", "subject", "product_filter"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return {"error": f"Missing required fields: {missing}"}, 400
        
        try:
            email_service = get_email_service()
            campaign = email_service.create_product_promotion_campaign(data)
            
            result = {
                "ok": True,
                "campaign_id": campaign.id,
                "name": campaign.name,
                "subject": campaign.subject,
                "campaign_type": campaign.campaign_type,
                "product_filter": campaign.product_filter,
                "status": campaign.status
            }
            
            # Auto-send if requested
            if data.get("auto_send", False):
                send_result = email_service.send_campaign(campaign.id)
                result["send_result"] = send_result
            
            return result, 201
            
        except Exception as e:
            return {"error": str(e)}, 400

@api.route("/win-back")
class EmailWinBack(Resource):
    @api.doc("create_winback_campaign")
    def post(self):
        """Create win-back campaign for inactive customers"""
        data = request.get_json()
        if not data:
            return {"error": "JSON data required"}, 400
        
        required_fields = ["name", "subject"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return {"error": f"Missing required fields: {missing}"}, 400
        
        try:
            email_service = get_email_service()
            campaign = email_service.create_winback_campaign(data)
            
            result = {
                "ok": True,
                "campaign_id": campaign.id,
                "name": campaign.name,
                "subject": campaign.subject,
                "campaign_type": campaign.campaign_type,
                "status": campaign.status
            }
            
            # Auto-send if requested
            if data.get("auto_send", False):
                send_result = email_service.send_campaign(campaign.id)
                result["send_result"] = send_result
            
            return result, 201
            
        except Exception as e:
            return {"error": str(e)}, 400

@api.route("/send/<int:campaign_id>")
@api.param("campaign_id", "Campaign ID")
class EmailSend(Resource):
    @api.doc("send_email_campaign")
    def post(self, campaign_id: int):
        """Send email campaign to all targeted customers"""
        try:
            email_service = get_email_service()
            result = email_service.send_campaign(campaign_id)
            
            if "error" in result:
                return result, 400
            
            return {"ok": True, **result}, 200
            
        except Exception as e:
            return {"error": str(e)}, 400

@api.route("/send-custom")
class EmailSendCustom(Resource):
    @api.doc("send_custom_email")
    def post(self):
        """Send custom email to all customers or specific segment"""
        data = request.get_json()
        if not data:
            return {"error": "JSON data required"}, 400
        
        required_fields = ["subject", "body"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return {"error": f"Missing required fields: {missing}"}, 400
        
        try:
            email_service = get_email_service()
            result = email_service.send_custom_email(
                subject=data["subject"],
                body=data["body"],
                segment=data.get("segment", "all"),  # all, loyal, high_value, frequent, at_risk, individual
                product_filter=data.get("product_filter"),
                sender_name=data.get("sender_name", "The Team"),
                customer_id=data.get("customer_id"),  # Required when segment="individual"
                customer_email=data.get("customer_email")  # Alternative to customer_id
            )
            
            if "error" in result:
                return result, 400
            
            return {"ok": True, **result}, 200
            
        except Exception as e:
            return {"error": str(e)}, 400