"""
Abstract Base Class for Broker OAuth Handlers
Provides common interface and utilities for broker-specific OAuth implementations
"""

import json
import boto3
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import os
import secrets
import hashlib

# Import shared logger
try:
    from shared_utils.logger import setup_logger, log_user_action, log_api_response
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

class BaseBrokerOAuthHandler(ABC):
    """
    Abstract base class for broker OAuth implementations
    Follows strategy pattern for broker-specific OAuth flows
    """
    
    def __init__(self, broker_name: str):
        """
        Initialize OAuth handler for specific broker
        
        Args:
            broker_name: Name of the broker (e.g., 'zerodha', 'angel', 'finvasia')
        """
        self.broker_name = broker_name.lower()
        self.dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        self.secretsmanager = boto3.client('secretsmanager', region_name=os.environ['REGION'])
        self.table = self.dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])
        
    # Abstract methods that each broker must implement
    
    @abstractmethod
    def get_oauth_url(self, api_key: str, state: str) -> str:
        """
        Generate broker-specific OAuth URL
        
        Args:
            api_key: Broker API key
            state: OAuth state parameter
            
        Returns:
            Complete OAuth URL for the broker
        """
        pass
    
    @abstractmethod
    def exchange_token(self, request_token: str, api_key: str, api_secret: str) -> Dict[str, Any]:
        """
        Exchange request token for access token
        
        Args:
            request_token: Token received from OAuth callback
            api_key: Broker API key
            api_secret: Broker API secret
            
        Returns:
            Dictionary containing access token and metadata
        """
        pass
    
    @abstractmethod
    def validate_callback_params(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate broker-specific callback parameters
        
        Args:
            params: Callback parameters from request body
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def get_token_expiry(self, token_data: Dict[str, Any]) -> datetime:
        """
        Get token expiry time based on broker-specific logic
        
        Args:
            token_data: Token data returned from broker
            
        Returns:
            Expiry datetime in UTC
        """
        pass
    
    @abstractmethod
    def check_token_validity(self, token_data: Dict[str, Any]) -> bool:
        """
        Check if stored token is still valid
        
        Args:
            token_data: Stored token data
            
        Returns:
            True if token is valid, False otherwise
        """
        pass
    
    # Common utility methods
    
    def generate_state(self, user_id: str, client_id: str) -> str:
        """
        Generate secure state parameter for OAuth
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            Secure state string
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        nonce = secrets.token_urlsafe(16)
        
        # Create deterministic but secure state
        state_data = f"{user_id}:{client_id}:{timestamp}:{nonce}"
        state_hash = hashlib.sha256(state_data.encode()).hexdigest()[:32]
        
        return state_hash
    
    def validate_state(self, state: str, user_id: str, client_id: str) -> bool:
        """
        Validate OAuth state parameter
        
        Args:
            state: State parameter from callback
            user_id: User ID
            client_id: Client ID
            
        Returns:
            True if state is valid, False otherwise
        """
        # In a production system, you'd store and validate against stored state
        # For now, we'll perform basic validation
        if not state or len(state) < 16:
            return False
        return True
    
    def get_broker_account(self, user_id: str, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve broker account from DynamoDB
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            Broker account data or None if not found
        """
        try:
            response = self.table.get_item(
                Key={
                    'user_id': user_id,
                    'client_id': client_id
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error("Failed to get broker account", extra={
                "error": str(e), 
                "user_id": user_id, 
                "client_id": client_id
            })
            return None
    
    def get_api_credentials(self, secret_arn: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve API credentials from Secrets Manager
        
        Args:
            secret_arn: ARN of the secret containing API credentials
            
        Returns:
            API credentials or None if retrieval fails
        """
        try:
            response = self.secretsmanager.get_secret_value(SecretId=secret_arn)
            return json.loads(response['SecretString'])
        except Exception as e:
            logger.error("Failed to retrieve API credentials", extra={
                "error": str(e),
                "secret_arn": secret_arn
            })
            return None
    
    def store_oauth_tokens(self, user_id: str, client_id: str, token_data: Dict[str, Any], 
                          api_key: str) -> Optional[str]:
        """
        Store OAuth tokens in Secrets Manager
        
        Args:
            user_id: User ID
            client_id: Client ID  
            token_data: Token data from broker
            api_key: Broker API key
            
        Returns:
            ARN of created secret or None if storage fails
        """
        try:
            # Create secret name following the pattern
            secret_name = f"ql-{self.broker_name}-oauth-tokens-{os.environ.get('STAGE', 'dev')}-{user_id}-{client_id}"
            
            # Prepare token data for storage
            token_expires_at = self.get_token_expiry(token_data)
            
            secret_data = {
                'access_token': token_data.get('access_token'),
                'api_key': api_key,
                'token_expires_at': token_expires_at.isoformat(),
                'last_oauth_login': datetime.now(timezone.utc).isoformat(),
                'session_valid': True,
                'client_id': client_id,
                'broker_name': self.broker_name,
                'user_id': user_id,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Add broker-specific data
            if 'refresh_token' in token_data:
                secret_data['refresh_token'] = token_data['refresh_token']
            if 'scope' in token_data:
                secret_data['scope'] = token_data['scope']
            
            # Store in Secrets Manager
            response = self.secretsmanager.create_secret(
                Name=secret_name,
                Description=f"{self.broker_name.title()} OAuth tokens for user {user_id} - client {client_id}",
                SecretString=json.dumps(secret_data)
            )
            
            return response['ARN']
            
        except self.secretsmanager.exceptions.ResourceExistsException:
            # Secret already exists, update it
            try:
                self.secretsmanager.update_secret(
                    SecretId=secret_name,
                    SecretString=json.dumps(secret_data)
                )
                
                # Get the ARN
                response = self.secretsmanager.describe_secret(SecretId=secret_name)
                return response['ARN']
                
            except Exception as e:
                logger.error("Failed to update OAuth tokens", extra={
                    "error": str(e),
                    "secret_name": secret_name
                })
                return None
        except Exception as e:
            logger.error("Failed to store OAuth tokens", extra={
                "error": str(e),
                "secret_name": secret_name
            })
            return None
    
    def get_oauth_tokens(self, user_id: str, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve OAuth tokens from Secrets Manager
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            OAuth token data or None if not found
        """
        try:
            secret_name = f"ql-{self.broker_name}-oauth-tokens-{os.environ.get('STAGE', 'dev')}-{user_id}-{client_id}"
            
            response = self.secretsmanager.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except self.secretsmanager.exceptions.ResourceNotFoundException:
            logger.info("OAuth tokens not found", extra={
                "user_id": user_id,
                "client_id": client_id,
                "broker": self.broker_name
            })
            return None
        except Exception as e:
            logger.error("Failed to retrieve OAuth tokens", extra={
                "error": str(e),
                "user_id": user_id,
                "client_id": client_id
            })
            return None
    
    def update_broker_account_oauth_status(self, user_id: str, client_id: str, 
                                         token_secret_arn: str, expires_at: datetime):
        """
        Update broker account with OAuth token information
        
        Args:
            user_id: User ID
            client_id: Client ID
            token_secret_arn: ARN of OAuth token secret
            expires_at: Token expiry time
        """
        try:
            self.table.update_item(
                Key={
                    'user_id': user_id,
                    'client_id': client_id
                },
                UpdateExpression="SET oauth_token_secret_arn = :arn, token_expires_at = :expires, last_oauth_login = :login, updated_at = :updated",
                ExpressionAttributeValues={
                    ':arn': token_secret_arn,
                    ':expires': expires_at.isoformat(),
                    ':login': datetime.now(timezone.utc).isoformat(),
                    ':updated': datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info("Updated broker account OAuth status", extra={
                "user_id": user_id,
                "client_id": client_id,
                "broker": self.broker_name
            })
            
        except Exception as e:
            logger.error("Failed to update broker account OAuth status", extra={
                "error": str(e),
                "user_id": user_id,
                "client_id": client_id
            })
    
    # Common HTTP response helpers
    
    def create_success_response(self, data: Dict[str, Any], message: str = "Success", 
                              status_code: int = 200) -> Dict[str, Any]:
        """Create standardized success response"""
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': data,
                'message': message
            })
        }
    
    def create_error_response(self, error: str, message: str, 
                            status_code: int = 400) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': error,
                'message': message
            })
        }
    
    # Main handler methods that use the abstract methods
    
    def handle_oauth_login(self, user_id: str, client_id: str) -> Dict[str, Any]:
        """
        Handle OAuth login initiation
        
        Args:
            user_id: User ID from JWT token
            client_id: Client ID from path parameters
            
        Returns:
            HTTP response with OAuth URL or error
        """
        try:
            # Get broker account
            account = self.get_broker_account(user_id, client_id)
            if not account:
                return self.create_error_response(
                    'Broker account not found',
                    'No broker account found with the provided client_id',
                    404
                )
            
            # Verify broker matches this handler
            if account['broker_name'] != self.broker_name:
                return self.create_error_response(
                    'Broker mismatch',
                    f'Account broker {account["broker_name"]} does not match handler {self.broker_name}',
                    400
                )
            
            # Get API credentials
            api_secret_arn = account.get('api_key_secret_arn')
            if not api_secret_arn:
                return self.create_error_response(
                    'No API credentials found',
                    'Please configure API credentials first',
                    400
                )
            
            credentials = self.get_api_credentials(api_secret_arn)
            if not credentials:
                return self.create_error_response(
                    'Failed to retrieve API credentials',
                    'Unable to access stored API credentials',
                    500
                )
            
            # Generate state and OAuth URL
            state = self.generate_state(user_id, client_id)
            oauth_url = self.get_oauth_url(credentials['api_key'], state)
            
            log_user_action(logger, user_id, "oauth_login_initiated", {
                "client_id": client_id,
                "broker_name": self.broker_name
            })
            
            return self.create_success_response({
                'oauth_url': oauth_url,
                'state': state,
                'expires_in': 300  # State expires in 5 minutes
            }, 'OAuth login URL generated successfully')
            
        except Exception as e:
            logger.error("Failed to initiate OAuth login", extra={
                "error": str(e), 
                "user_id": user_id,
                "client_id": client_id,
                "broker": self.broker_name
            })
            return self.create_error_response(
                'Failed to initiate OAuth login',
                str(e),
                500
            )
    
    def handle_oauth_callback(self, user_id: str, client_id: str, 
                            callback_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle OAuth callback and token exchange
        
        Args:
            user_id: User ID from JWT token
            client_id: Client ID from path parameters
            callback_params: Parameters from callback request
            
        Returns:
            HTTP response with token data or error
        """
        try:
            # Validate callback parameters
            is_valid, error_msg = self.validate_callback_params(callback_params)
            if not is_valid:
                return self.create_error_response(
                    'Invalid callback parameters',
                    error_msg,
                    400
                )
            
            # Validate state
            state = callback_params.get('state', '')
            if not self.validate_state(state, user_id, client_id):
                return self.create_error_response(
                    'Invalid state parameter',
                    'State parameter is invalid or has expired',
                    400
                )
            
            # Get broker account and credentials
            account = self.get_broker_account(user_id, client_id)
            if not account:
                return self.create_error_response(
                    'Broker account not found',
                    'No broker account found with the provided client_id',
                    404
                )
            
            credentials = self.get_api_credentials(account['api_key_secret_arn'])
            if not credentials:
                return self.create_error_response(
                    'Failed to retrieve API credentials',
                    'Unable to access stored API credentials',
                    500
                )
            
            # Exchange token using broker-specific logic
            request_token = callback_params.get('request_token')
            token_data = self.exchange_token(
                request_token, 
                credentials['api_key'], 
                credentials['api_secret']
            )
            
            # Store OAuth tokens
            token_secret_arn = self.store_oauth_tokens(
                user_id, client_id, token_data, credentials['api_key']
            )
            
            if not token_secret_arn:
                return self.create_error_response(
                    'Failed to store OAuth tokens',
                    'Unable to store authentication tokens',
                    500
                )
            
            # Update broker account
            expires_at = self.get_token_expiry(token_data)
            self.update_broker_account_oauth_status(
                user_id, client_id, token_secret_arn, expires_at
            )
            
            log_user_action(logger, user_id, "oauth_callback_success", {
                "client_id": client_id,
                "broker_name": self.broker_name
            })
            
            return self.create_success_response({
                'token_expires_at': expires_at.isoformat(),
                'valid_until': expires_at.isoformat(),
                'session_valid': True
            }, 'OAuth authentication successful')
            
        except Exception as e:
            logger.error("OAuth callback failed", extra={
                "error": str(e),
                "user_id": user_id,
                "client_id": client_id,
                "broker": self.broker_name
            })
            return self.create_error_response(
                'OAuth callback failed',
                str(e),
                500
            )
    
    def handle_oauth_status(self, user_id: str, client_id: str) -> Dict[str, Any]:
        """
        Get OAuth authentication status
        
        Args:
            user_id: User ID from JWT token
            client_id: Client ID from path parameters
            
        Returns:
            HTTP response with OAuth status
        """
        try:
            # Get OAuth tokens
            tokens = self.get_oauth_tokens(user_id, client_id)
            
            if not tokens:
                return self.create_success_response({
                    'has_token': False,
                    'is_valid': False,
                    'requires_login': True
                }, 'No OAuth tokens found')
            
            # Check token validity
            is_valid = self.check_token_validity(tokens)
            expires_at = tokens.get('token_expires_at')
            last_login = tokens.get('last_oauth_login')
            
            return self.create_success_response({
                'has_token': True,
                'is_valid': is_valid,
                'requires_login': not is_valid,
                'expires_at': expires_at,
                'last_login': last_login
            }, 'OAuth status retrieved successfully')
            
        except Exception as e:
            logger.error("Failed to get OAuth status", extra={
                "error": str(e),
                "user_id": user_id,
                "client_id": client_id,
                "broker": self.broker_name
            })
            return self.create_error_response(
                'Failed to get OAuth status',
                str(e),
                500
            )