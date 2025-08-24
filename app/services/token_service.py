import base64
import logging

logger = logging.getLogger(__name__)

class TokenService:
    """Simple token encoding/decoding service - can be enhanced with proper encryption later"""
    
    @staticmethod
    def encode_token(token):
        """Encode token for storage"""
        try:
            if not token:
                raise ValueError("Token is empty or None")
            return base64.b64encode(token.encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding token: {e}")
            raise
    
    @staticmethod
    def decode_token(encoded_token):
        """Decode token for use"""
        try:
            # Handle both encoded and plain text tokens for backward compatibility
            if not encoded_token:
                raise ValueError("Token is empty or None")
            
            # Try to decode as base64 first
            try:
                decoded_bytes = base64.b64decode(encoded_token.encode('utf-8'))
                decoded_token = decoded_bytes.decode('utf-8')
                logger.info(f"Successfully decoded base64 token. Length: {len(decoded_token)}")
                return decoded_token
            except Exception as decode_error:
                logger.warning(f"Base64 decode failed: {decode_error}. Treating as plain text token.")
                # If base64 decoding fails, assume it's already a plain text token
                logger.info(f"Using plain text token. Length: {len(encoded_token)}")
                return encoded_token
                
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            raise
    
    @staticmethod
    def is_valid_base64(encoded_token):
        """Check if token is valid base64"""
        try:
            if not encoded_token:
                return False
            base64.b64decode(encoded_token.encode('utf-8')).decode('utf-8')
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_token(token):
        """Validate that a token looks like a valid Notion token"""
        if not token:
            return False
        # Notion tokens typically start with 'secret_' and are quite long
        if isinstance(token, str) and len(token) > 20:
            return True
        return False