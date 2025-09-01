"""
Zerodha OAuth Strategy Implementation
Handles Zerodha Kite Connect specific OAuth flow
"""

import json
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional
import hashlib

from base_broker_oauth_handler import BaseBrokerOAuthHandler
from broker_configs import get_broker_config

# Import shared logger
try:
    from shared_utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class ZerodhaOAuthStrategy(BaseBrokerOAuthHandler):
    """
    Zerodha Kite Connect OAuth strategy implementation
    Handles popup-based OAuth flow with daily session tokens
    """
    
    def __init__(self):
        super().__init__('zerodha')
        self.config = get_broker_config('zerodha')
        
        if not self.config:
            raise ValueError("Zerodha configuration not found")
    
    def get_oauth_url(self, api_key: str, state: str) -> str:
        """
        Generate Zerodha OAuth URL for popup flow
        
        Args:
            api_key: Zerodha API key
            state: OAuth state parameter
            
        Returns:
            Complete Zerodha OAuth URL
        """
        # Zerodha OAuth URL format
        # Frontend will append &redirect_uri={callback_url} to this URL
        return f"{self.config.oauth_base_url}?api_key={api_key}&state={state}"
    
    def validate_callback_params(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate Zerodha-specific callback parameters
        
        Args:
            params: Callback parameters from request body
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for OAuth error status
        if params.get('status') == 'error':
            return False, "OAuth authentication was cancelled or failed"
        
        # Zerodha must provide request_token
        request_token = params.get('request_token')
        if not request_token:
            return False, "No request token received from Zerodha. Please try again."
        
        # Validate request token format (basic validation)
        if len(request_token) < 10:
            return False, "Invalid request token format received from Zerodha"
        
        return True, None
    
    def exchange_token(self, request_token: str, api_key: str, api_secret: str) -> Dict[str, Any]:
        """
        Exchange Zerodha request token for access token
        
        Args:
            request_token: Token received from OAuth callback
            api_key: Zerodha API key
            api_secret: Zerodha API secret
            
        Returns:
            Dictionary containing access token and metadata
        """
        try:
            # Generate checksum for Zerodha token exchange
            checksum_data = f"{api_key}{request_token}{api_secret}"
            checksum = hashlib.sha256(checksum_data.encode()).hexdigest()
            
            # Prepare token exchange request
            token_url = self.config.token_exchange_url
            payload = {
                "api_key": api_key,
                "request_token": request_token,
                "checksum": checksum
            }
            
            logger.info("Exchanging request token for access token", extra={
                "api_key": api_key,
                "request_token_length": len(request_token),
                "broker": self.broker_name
            })
            
            # Make request to Zerodha token exchange endpoint
            response = requests.post(token_url, data=payload, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Validate response format
            if 'data' not in token_data or 'access_token' not in token_data['data']:
                raise ValueError("Invalid token response format from Zerodha")
            
            access_token = token_data['data']['access_token']
            
            # Log successful token exchange (without token value)
            logger.info("Successfully exchanged request token", extra={
                "api_key": api_key,
                "has_access_token": bool(access_token),
                "broker": self.broker_name
            })
            
            return {
                'access_token': access_token,
                'token_type': 'session',
                'broker_response': token_data['data']  # Store full response for any additional data
            }
            
        except requests.exceptions.RequestException as e:
            logger.error("Network error during token exchange", extra={
                "error": str(e),
                "api_key": api_key,
                "broker": self.broker_name
            })
            raise Exception(f"Network error during token exchange: {str(e)}")
        
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error during token exchange", extra={
                "error": str(e),
                "status_code": e.response.status_code if e.response else None,
                "api_key": api_key,
                "broker": self.broker_name
            })
            
            # Try to parse error response
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message', 'Token exchange failed')
            except:
                error_msg = f"HTTP {e.response.status_code}: Token exchange failed"
            
            raise Exception(error_msg)
        
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.error("Invalid response format during token exchange", extra={
                "error": str(e),
                "api_key": api_key,
                "broker": self.broker_name
            })
            raise Exception(f"Invalid response from Zerodha: {str(e)}")
        
        except Exception as e:
            logger.error("Unexpected error during token exchange", extra={
                "error": str(e),
                "api_key": api_key,
                "broker": self.broker_name
            })
            raise Exception(f"Token exchange failed: {str(e)}")
    
    def get_token_expiry(self, token_data: Dict[str, Any]) -> datetime:
        """
        Get Zerodha token expiry time (daily at 6 AM IST)
        
        Args:
            token_data: Token data returned from broker
            
        Returns:
            Expiry datetime in UTC
        """
        # Zerodha tokens expire daily at 6:00 AM IST
        # Calculate next 6 AM IST in UTC
        
        now_utc = datetime.now(timezone.utc)
        
        # Convert to IST (UTC+5:30)
        ist_offset = timedelta(hours=5, minutes=30)
        now_ist = now_utc + ist_offset
        
        # Get next 6 AM IST
        next_6am_ist = now_ist.replace(hour=6, minute=0, second=0, microsecond=0)
        
        # If current time is past 6 AM IST today, move to tomorrow
        if now_ist.hour >= 6:
            next_6am_ist += timedelta(days=1)
        
        # Convert back to UTC
        next_6am_utc = next_6am_ist - ist_offset
        
        logger.info("Calculated token expiry", extra={
            "current_utc": now_utc.isoformat(),
            "expiry_utc": next_6am_utc.isoformat(),
            "broker": self.broker_name
        })
        
        return next_6am_utc
    
    def check_token_validity(self, token_data: Dict[str, Any]) -> bool:
        """
        Check if stored Zerodha token is still valid
        
        Args:
            token_data: Stored token data
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Check if token exists
            if not token_data.get('access_token'):
                return False
            
            # Check expiry time
            expires_at_str = token_data.get('token_expires_at')
            if not expires_at_str:
                return False
            
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            now_utc = datetime.now(timezone.utc)
            
            # Token is valid if it hasn't expired
            is_valid = now_utc < expires_at
            
            logger.info("Token validity check", extra={
                "is_valid": is_valid,
                "expires_at": expires_at.isoformat(),
                "current_time": now_utc.isoformat(),
                "broker": self.broker_name
            })
            
            return is_valid
            
        except (ValueError, TypeError) as e:
            logger.error("Error checking token validity", extra={
                "error": str(e),
                "broker": self.broker_name
            })
            return False
    
    def validate_api_credentials_format(self, api_key: str, api_secret: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Zerodha API credentials format
        
        Args:
            api_key: Zerodha API key
            api_secret: Zerodha API secret
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Import here to avoid circular imports
        from broker_configs import validate_api_credentials
        return validate_api_credentials('zerodha', api_key, api_secret)
    
    def test_api_connection(self, api_key: str, access_token: str) -> Tuple[bool, Optional[str]]:
        """
        Test Zerodha API connection with access token
        
        Args:
            api_key: Zerodha API key
            access_token: Zerodha access token
            
        Returns:
            Tuple of (is_connected, error_message)
        """
        try:
            # Test connection by calling Zerodha profile API
            headers = {
                'Authorization': f'token {api_key}:{access_token}',
                'X-Kite-Version': '3'
            }
            
            response = requests.get(
                'https://api.kite.trade/user/profile',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                profile_data = response.json()
                
                if 'data' in profile_data:
                    logger.info("API connection test successful", extra={
                        "api_key": api_key,
                        "user_name": profile_data['data'].get('user_name', 'Unknown'),
                        "broker": self.broker_name
                    })
                    return True, None
                else:
                    return False, "Invalid response format from Zerodha API"
            else:
                logger.warning("API connection test failed", extra={
                    "api_key": api_key,
                    "status_code": response.status_code,
                    "broker": self.broker_name
                })
                return False, f"API connection failed with status {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "API connection timeout"
        except requests.exceptions.RequestException as e:
            return False, f"API connection error: {str(e)}"
        except Exception as e:
            logger.error("Unexpected error during API connection test", extra={
                "error": str(e),
                "api_key": api_key,
                "broker": self.broker_name
            })
            return False, f"Connection test failed: {str(e)}"
    
    def get_user_profile(self, api_key: str, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from Zerodha API
        
        Args:
            api_key: Zerodha API key
            access_token: Zerodha access token
            
        Returns:
            User profile data or None if failed
        """
        try:
            headers = {
                'Authorization': f'token {api_key}:{access_token}',
                'X-Kite-Version': '3'
            }
            
            response = requests.get(
                'https://api.kite.trade/user/profile',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Failed to get user profile", extra={
                    "status_code": response.status_code,
                    "broker": self.broker_name
                })
                return None
                
        except Exception as e:
            logger.error("Error getting user profile", extra={
                "error": str(e),
                "broker": self.broker_name
            })
            return None
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Zerodha doesn't support token refresh - tokens expire daily
        
        Args:
            refresh_token: Not used for Zerodha
            
        Returns:
            Error response indicating refresh is not supported
        """
        raise Exception("Zerodha tokens cannot be refreshed - please re-authenticate")
    
    def revoke_token(self, access_token: str) -> bool:
        """
        Zerodha doesn't support explicit token revocation
        
        Args:
            access_token: Token to revoke
            
        Returns:
            False as revocation is not supported
        """
        logger.warning("Token revocation not supported", extra={
            "broker": self.broker_name
        })
        return False