from ..models.dt_company_com import DtCompanyCom
from ..models.dt_user_detail import DtUserDetail
from ..models.dt_notion_account import DtNotionAccount
from ..extensions import db

class CompanyRepository:
    
    @staticmethod
    def get_user_company(user_id):
        """Get user's company context"""
        user_detail = DtUserDetail.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).first()
        return user_detail.company if user_detail else None
    
    @staticmethod
    def get_notion_config(com_id):
        """Get active Notion configuration for company"""
        return DtNotionAccount.query.filter_by(
            com_id=com_id,
            is_active=True
        ).first()
    
    @staticmethod
    def create_company(name, code, description=None):
        """Create new company"""
        company = DtCompanyCom(
            com_name=name,
            com_code=code,
            com_description=description
        )
        db.session.add(company)
        db.session.flush()
        return company
    
    @staticmethod
    def add_user_to_company(user_id, com_id, role='member'):
        """Add user to company"""
        user_detail = DtUserDetail(
            user_id=user_id,
            com_id=com_id,
            user_role=role
        )
        db.session.add(user_detail)
        return user_detail
    
    @staticmethod
    def create_notion_account(com_id, token, parent_page_id, workspace_name):
        """Create Notion account for company"""
        # from ..services.token_service import TokenService  # TODO: Re-enable when encryption is implemented
        
        notion_account = DtNotionAccount(
            com_id=com_id,
            notion_token=token,  # Store as plain text for now
            # notion_token=TokenService.encode_token(token),  # TODO: Re-enable when encryption is implemented
            notion_parent_page_id=parent_page_id,
            workspace_name=workspace_name
        )
        db.session.add(notion_account)
        db.session.flush()
        return notion_account
    
    @staticmethod
    def update_notion_token(com_id, new_token):
        """Update Notion token for company"""
        # from ..services.token_service import TokenService  # TODO: Re-enable when encryption is implemented
        
        notion_account = DtNotionAccount.query.filter_by(
            com_id=com_id,
            is_active=True
        ).first()
        
        if notion_account:
            notion_account.notion_token = new_token  # Store as plain text for now
            # notion_account.notion_token = TokenService.encode_token(new_token)  # TODO: Re-enable when encryption is implemented
            db.session.flush()
            return notion_account
        return None
    
    @staticmethod
    def validate_notion_token(com_id):
        """Validate and test Notion token for company"""
        # from ..services.token_service import TokenService  # TODO: Re-enable when encryption is implemented
        from notion_client import Client
        
        notion_account = CompanyRepository.get_notion_config(com_id)
        if not notion_account:
            return {"valid": False, "error": "No Notion configuration found"}
        
        try:
            # Use plain text token directly
            token = notion_account.notion_token
            # token = TokenService.decode_token(notion_account.notion_token)  # TODO: Re-enable when encryption is implemented
            
            # Try to create client and make a simple API call
            client = Client(auth=token)
            # Test with a simple API call
            client.users.me()
            
            return {"valid": True, "token_length": len(token)}
        except Exception as e:
            return {"valid": False, "error": str(e), "token_preview": str(notion_account.notion_token)[:20]}