"""
Zebu MYNT OAuth Strategy Implementation
Handles Zebu MYNT API specific OAuth flow
Documentation: https://api.zebuetrade.com/OAuth/
Reference: myntapi Python library (https://pypi.org/project/myntapi/)
"""

import json
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional

from base_broker_oauth_handler import BaseBrokerOAuthHandler
from broker_configs import get_broker_config

# Import shared logger
try:
    from shared_utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ZebuOAuthStrategy(BaseBrokerOAuthHandler):
    """
    Zebu MYNT API OAuth strategy implementation
    Handles popup-based OAuth flow with refreshable bearer tokens

    Credentials (from go.mynt.in OAuth app registration):
    - client_id: OAuth Client ID (stored in api_key field)
    - client_secret: OAuth Client Secret (stored in api_secret field)

    OAuth Flow:
    1. User redirected to: https://go.mynt.in/OAuthlogin/authorize/oauth?client_id={client_id}
    2. User logs in and authorizes
    3. Redirect to callback URL with authorization code
    4. Exchange code for access_token using client_id + client_secret + code
    5. Access token can be refreshed using refresh_token
    """

    # Zebu OAuth API endpoints (based on myntapi library)
    OAUTH_TOKEN_URL = 'https://go.mynt.in/NorenWClientAPI/GenAcsTok'
    TOKEN_REFRESH_URL = 'https://go.mynt.in/NorenWClientAPI/RefreshToken'

    def __init__(self):
        super().__init__('zebu')
        self.config = get_broker_config('zebu')

        if not self.config:
            raise ValueError("Zebu configuration not found")

    def get_oauth_url(self, api_key: str, state: str) -> str:
        """
        Generate Zebu OAuth URL for popup flow

        Args:
            api_key: Client ID from go.mynt.in OAuth app (stored in api_key field)
            state: OAuth state parameter for CSRF protection

        Returns:
            Complete Zebu OAuth URL
        """
        # Zebu OAuth URL format - uses client_id parameter
        # Frontend will append redirect_uri
        return f"{self.config.oauth_base_url}?client_id={api_key}"

    def validate_callback_params(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate Zebu-specific callback parameters

        Args:
            params: Callback parameters from request body

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for OAuth error
        if params.get('error'):
            error_desc = params.get('error_description', 'OAuth authentication failed')
            return False, f"OAuth error: {error_desc}"

        # Zebu returns authorization code
        code = params.get('code') or params.get('request_token')
        if not code:
            return False, "No authorization code received from Zebu. Please try again."

        # Basic validation of code format
        if len(code) < 5:
            return False, "Invalid authorization code format received from Zebu"

        return True, None

    def exchange_token(self, request_token: str, api_key: str, api_secret: str) -> Dict[str, Any]:
        """
        Exchange Zebu authorization code for access token
        Based on myntapi library's __get_access_token method

        Args:
            request_token: Authorization code received from OAuth callback
            api_key: Client ID from go.mynt.in (stored in api_key field)
            api_secret: Client Secret from go.mynt.in (stored in api_secret field)

        Returns:
            Dictionary containing access token and metadata
        """
        try:
            # Generate checksum: SHA256(client_id + client_secret + code)
            # This matches the myntapi library implementation
            checksum_data = f"{api_key}{api_secret}{request_token}"
            checksum = hashlib.sha256(checksum_data.encode()).hexdigest()

            # Zebu expects: jData={"code":"...", "checksum":"..."}
            # Content-Type: text/plain (not JSON!)
            payload_dict = {
                "code": request_token,
                "checksum": checksum
            }
            payload = f'jData={json.dumps(payload_dict)}'

            logger.info("Exchanging authorization code for access token", extra={
                "client_id": api_key[:8] + "***" if len(api_key) > 8 else "***",
                "code_length": len(request_token),
                "checksum_length": len(checksum),
                "broker": self.broker_name
            })

            # Make request to Zebu OAuth token endpoint
            # Zebu requires Content-Type: text/plain with jData= prefix
            headers = {
                'Content-Type': 'text/plain'
            }

            response = requests.post(
                self.OAUTH_TOKEN_URL,
                data=payload,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()

            token_data = response.json()

            # Validate response - Zebu returns stat="Ok" on success
            if token_data.get('stat') != 'Ok':
                error_msg = token_data.get('emsg', 'Token exchange failed')
                raise ValueError(f"Zebu token exchange failed: {error_msg}")

            # Zebu returns susertoken as the access token
            access_token = token_data.get('susertoken') or token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            # Default to 1 hour if not specified
            expires_in = token_data.get('expires_in', 3600)

            if not access_token:
                raise ValueError("No access token (susertoken) in Zebu response")

            logger.info("Successfully exchanged authorization code", extra={
                "client_id": api_key[:8] + "***" if len(api_key) > 8 else "***",
                "has_access_token": bool(access_token),
                "has_refresh_token": bool(refresh_token),
                "expires_in": expires_in,
                "user_id": token_data.get('uid', 'unknown'),
                "broker": self.broker_name
            })

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer',
                'expires_in': expires_in,
                'user_id': token_data.get('uid'),
                'broker_response': token_data
            }

        except requests.exceptions.RequestException as e:
            logger.error("Network error during token exchange", extra={
                "error": str(e),
                "client_id": api_key[:8] + "***" if len(api_key) > 8 else "***",
                "broker": self.broker_name
            })
            raise Exception(f"Network error during token exchange: {str(e)}")

        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error during token exchange", extra={
                "error": str(e),
                "status_code": e.response.status_code if e.response else None,
                "broker": self.broker_name
            })

            try:
                error_data = e.response.json()
                error_msg = error_data.get('emsg', 'Token exchange failed')
            except:
                error_msg = f"HTTP {e.response.status_code}: Token exchange failed"

            raise Exception(error_msg)

        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.error("Invalid response format during token exchange", extra={
                "error": str(e),
                "broker": self.broker_name
            })
            raise Exception(f"Invalid response from Zebu: {str(e)}")

        except Exception as e:
            logger.error("Unexpected error during token exchange", extra={
                "error": str(e),
                "broker": self.broker_name
            })
            raise Exception(f"Token exchange failed: {str(e)}")

    def get_token_expiry(self, token_data: Dict[str, Any]) -> datetime:
        """
        Get Zebu token expiry time

        Args:
            token_data: Token data returned from broker

        Returns:
            Expiry datetime in UTC
        """
        # Zebu returns expires_in which could be:
        # 1. A Unix timestamp (epoch seconds) - large number like 1773242619
        # 2. Seconds until expiry - small number like 3600
        # 3. A string that needs to be converted to int
        expires_in_raw = token_data.get('expires_in', 3600)

        # Convert to int if string
        try:
            expires_in = int(expires_in_raw)
        except (ValueError, TypeError):
            expires_in = 3600  # Default to 1 hour if conversion fails

        now_utc = datetime.now(timezone.utc)

        # If expires_in is a Unix timestamp (> year 2020 in epoch = 1577836800)
        # treat it as absolute expiry time, otherwise treat as seconds from now
        if expires_in > 1577836800:
            # It's a Unix timestamp - convert directly to datetime
            expiry_utc = datetime.fromtimestamp(expires_in, tz=timezone.utc)
        else:
            # It's seconds until expiry
            expiry_utc = now_utc + timedelta(seconds=expires_in)

        logger.info("Calculated token expiry", extra={
            "current_utc": now_utc.isoformat(),
            "expiry_utc": expiry_utc.isoformat(),
            "expires_in_raw": str(expires_in_raw),
            "expires_in_parsed": expires_in,
            "is_timestamp": expires_in > 1577836800,
            "broker": self.broker_name
        })

        return expiry_utc

    def check_token_validity(self, token_data: Dict[str, Any]) -> bool:
        """
        Check if stored Zebu token is still valid

        Args:
            token_data: Stored token data

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Check if access token exists
            if not token_data.get('access_token'):
                return False

            # Check expiry time
            expires_at_str = token_data.get('token_expires_at')
            if not expires_at_str:
                # If no expiry, consider token valid if it exists
                return bool(token_data.get('access_token'))

            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            now_utc = datetime.now(timezone.utc)

            # Add 5 minute buffer - consider expired 5 minutes before actual expiry
            is_valid = now_utc < (expires_at - timedelta(minutes=5))

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
        Validate Zebu OAuth credentials format

        Args:
            api_key: Client ID from go.mynt.in OAuth app
            api_secret: Client Secret from go.mynt.in OAuth app

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation for Zebu OAuth credentials
        if not api_key or len(api_key) < 5:
            return False, "Invalid Client ID format for Zebu"

        if not api_secret or len(api_secret) < 10:
            return False, "Invalid Client Secret format for Zebu"

        return True, None

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Zebu access token using refresh token

        Args:
            refresh_token: Refresh token from previous authentication

        Returns:
            Dictionary containing new access token and metadata
        """
        try:
            payload = {
                "refresh_token": refresh_token
            }

            logger.info("Refreshing access token", extra={
                "has_refresh_token": bool(refresh_token),
                "broker": self.broker_name
            })

            headers = {
                'Content-Type': 'text/plain'
            }

            response = requests.post(
                self.TOKEN_REFRESH_URL,
                data=f"jData={json.dumps(payload)}",
                headers=headers,
                timeout=30
            )

            response.raise_for_status()

            token_data = response.json()

            if token_data.get('stat') != 'Ok':
                error_msg = token_data.get('emsg', 'Token refresh failed')
                raise ValueError(f"Zebu token refresh failed: {error_msg}")

            access_token = token_data.get('access_token')
            new_refresh_token = token_data.get('refresh_token', refresh_token)
            expires_in = token_data.get('expires_in', 3600)

            if not access_token:
                raise ValueError("No access token in Zebu refresh response")

            logger.info("Successfully refreshed access token", extra={
                "has_access_token": bool(access_token),
                "has_new_refresh_token": new_refresh_token != refresh_token,
                "expires_in": expires_in,
                "broker": self.broker_name
            })

            return {
                'access_token': access_token,
                'refresh_token': new_refresh_token,
                'token_type': 'bearer',
                'expires_in': expires_in,
                'broker_response': token_data
            }

        except requests.exceptions.RequestException as e:
            logger.error("Network error during token refresh", extra={
                "error": str(e),
                "broker": self.broker_name
            })
            raise Exception(f"Network error during token refresh: {str(e)}")

        except Exception as e:
            logger.error("Unexpected error during token refresh", extra={
                "error": str(e),
                "broker": self.broker_name
            })
            raise Exception(f"Token refresh failed: {str(e)}")

    def test_api_connection(self, api_key: str, access_token: str) -> Tuple[bool, Optional[str]]:
        """
        Test Zebu API connection with access token

        Args:
            api_key: Zebu API key (Vendor Code)
            access_token: Zebu access token

        Returns:
            Tuple of (is_connected, error_message)
        """
        try:
            # Test connection by calling Zebu user details API
            # Zebu uses Authorization: Bearer {token} header
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # Use a simple API call to verify token is working
            # Zebu may have different endpoint - adjust as needed
            response = requests.get(
                'https://go.mynt.in/NorenWClientAPI/UserDetails',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('stat') == 'Ok':
                    logger.info("API connection test successful", extra={
                        "api_key": api_key[:8] + "***" if len(api_key) > 8 else "***",
                        "broker": self.broker_name
                    })
                    return True, None
                else:
                    return False, data.get('emsg', 'API validation failed')
            else:
                logger.warning("API connection test failed", extra={
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
                "broker": self.broker_name
            })
            return False, f"Connection test failed: {str(e)}"

    def revoke_token(self, access_token: str) -> bool:
        """
        Zebu doesn't support explicit token revocation

        Args:
            access_token: Token to revoke

        Returns:
            False as revocation is not supported
        """
        logger.warning("Token revocation not supported", extra={
            "broker": self.broker_name
        })
        return False

    def get_user_profile(self, api_key: str, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from Zebu API

        Args:
            api_key: Zebu API key (Vendor Code)
            access_token: Zebu access token

        Returns:
            User profile data or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                'https://go.mynt.in/NorenWClientAPI/UserDetails',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('stat') == 'Ok':
                    return data
                else:
                    logger.warning("Failed to get user profile", extra={
                        "error": data.get('emsg'),
                        "broker": self.broker_name
                    })
                    return None
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
