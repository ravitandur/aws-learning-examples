import json
import boto3
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import os
import sys
import urllib.parse
import hashlib
import secrets
import requests

# Add paths for imports
sys.path.append('/opt/python')

# Import shared logger (copied during deployment)
try:
    from shared_utils.logger import setup_logger, log_lambda_event, log_user_action, log_api_response, sanitize_event
    logger = setup_logger(__name__)
except ImportError:
    # Fallback to basic logging if shared_utils not available
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(handler)
    
    # Create fallback functions
    def log_lambda_event(logger, event, context):
        logger.info(f"Lambda invocation started")
        
    def log_user_action(logger, user_id, action, details=None):
        logger.info(f"User {user_id} performed action: {action}")
        
    def log_api_response(logger, status_code, user_id=None, response_size=None):
        logger.info(f"API response: {status_code}")

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to handle Zerodha OAuth flow
    Supports: /oauth/login, /oauth/callback, /oauth/status
    """
    
    # Log the incoming Lambda event (sanitized)
    log_lambda_event(logger, event, context)
    
    try:
        # Get user ID from Cognito authorizer context
        user_id = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            claims = event['requestContext']['authorizer'].get('claims', {})
            user_id = claims.get('sub') or claims.get('cognito:username')
        
        if not user_id:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Unauthorized',
                    'message': 'User ID not found in request context'
                })
            }
        
        # Get HTTP method and path parameters
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        client_id = path_parameters.get('client_id')
        oauth_action = path_parameters.get('oauth_action')  # login, callback, status
        
        logger.info("Processing OAuth request", extra={
            "user_id": user_id, 
            "http_method": http_method,
            "oauth_action": oauth_action,
            "client_id": client_id
        })
        
        if not client_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing client_id',
                    'message': 'client_id is required for OAuth operations'
                })
            }
        
        # Initialize AWS clients
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        secretsmanager = boto3.client('secretsmanager', region_name=os.environ['REGION'])
        broker_accounts_table = dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])
        
        # Route based on OAuth action
        if oauth_action == 'login' and http_method == 'POST':
            return handle_oauth_login(user_id, client_id, broker_accounts_table, secretsmanager)
        elif oauth_action == 'callback' and http_method == 'POST':
            return handle_oauth_callback(event, user_id, client_id, broker_accounts_table, secretsmanager)
        elif oauth_action == 'status' and http_method == 'GET':
            return handle_oauth_status(user_id, client_id, broker_accounts_table, secretsmanager)
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Method not allowed',
                    'message': f'OAuth action {oauth_action} with method {http_method} not supported'
                })
            }
            
    except Exception as e:
        logger.error("Unexpected error in OAuth handler", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

def handle_oauth_login(user_id, client_id, table, secretsmanager):
    """Initiate OAuth login flow for Zerodha"""
    
    try:
        # Get broker account to verify it exists
        response = table.get_item(
            Key={
                'user_id': user_id,
                'client_id': client_id
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Broker account not found'
                })
            }
        
        account = response['Item']
        
        # Only support Zerodha for now
        if account['broker_name'] != 'zerodha':
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'OAuth not supported',
                    'message': 'OAuth is currently only supported for Zerodha accounts'
                })
            }
        
        # Get API credentials
        api_secret_arn = account.get('api_key_secret_arn')
        if not api_secret_arn:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'No API credentials found',
                    'message': 'Please configure API credentials first'
                })
            }
        
        try:
            # Get API key from secrets using the full ARN
            secret_response = secretsmanager.get_secret_value(SecretId=api_secret_arn)
            credentials = json.loads(secret_response['SecretString'])
            api_key = credentials['api_key']
            
        except Exception as e:
            logger.error("Failed to retrieve API credentials", extra={"error": str(e), "user_id": user_id})
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Failed to retrieve API credentials',
                    'message': str(e)
                })
            }
        
        # Generate secure state parameter for OAuth
        state = secrets.token_urlsafe(32)
        
        # Store state temporarily (you might want to use DynamoDB or Redis for this)
        # For now, we'll include user_id and client_id in the state
        state_data = {
            'user_id': user_id,
            'client_id': client_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'nonce': secrets.token_urlsafe(16)
        }
        
        # Create OAuth URL for Zerodha (redirect_uri will be added by frontend)
        # Note: Frontend will append &redirect_uri={callback_url} to this URL
        oauth_url = f"https://kite.zerodha.com/connect/login?api_key={api_key}&state={state}"
        
        log_user_action(logger, user_id, "oauth_login_initiated", {
            "client_id": client_id,
            "broker_name": "zerodha"
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': {
                    'oauth_url': oauth_url,
                    'state': state,
                    'expires_in': 300  # State expires in 5 minutes
                },
                'message': 'OAuth login URL generated successfully'
            })
        }
        
    except Exception as e:
        logger.error("Failed to initiate OAuth login", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to initiate OAuth login',
                'message': str(e)
            })
        }

def handle_oauth_callback(event, user_id, client_id, table, secretsmanager):
    """Handle OAuth callback and exchange request token for access token"""
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        request_token = body.get('request_token')
        state = body.get('state')
        
        if not request_token:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required parameters',
                    'message': 'request_token is required'
                })
            }
        
        # Validate state parameter (in production, you'd validate against stored state)
        # For now, we'll proceed with the assumption that state is valid
        
        # Get broker account
        response = table.get_item(
            Key={
                'user_id': user_id,
                'client_id': client_id
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Broker account not found'
                })
            }
        
        account = response['Item']
        
        # Get API credentials
        api_secret_arn = account.get('api_key_secret_arn')
        if not api_secret_arn:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'No API credentials found'
                })
            }
        
        try:
            # Get API credentials from secrets using the full ARN
            secret_response = secretsmanager.get_secret_value(SecretId=api_secret_arn)
            credentials = json.loads(secret_response['SecretString'])
            api_key = credentials['api_key']
            api_secret = credentials['api_secret']
            
        except Exception as e:
            logger.error("Failed to retrieve API credentials", extra={"error": str(e), "user_id": user_id})
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Failed to retrieve API credentials'
                })
            }
        
        # Exchange request_token for access_token using Zerodha API
        try:
            logger.info("Starting token exchange", extra={
                "user_id": user_id, 
                "client_id": client_id,
                "request_token_length": len(request_token) if request_token else 0,
                "api_key_length": len(api_key) if api_key else 0
            })
            
            access_token = exchange_request_token_for_access_token(
                api_key, api_secret, request_token
            )
            
            logger.info("Token exchange successful", extra={
                "user_id": user_id,
                "client_id": client_id,
                "access_token_length": len(access_token) if access_token else 0
            })
            
        except Exception as e:
            logger.error("Failed to exchange request token", extra={
                "error": str(e), 
                "user_id": user_id,
                "client_id": client_id,
                "request_token_prefix": request_token[:8] + "..." if request_token and len(request_token) > 8 else request_token
            })
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Token exchange failed',
                    'message': str(e)
                })
            }
        
        current_time = datetime.now(timezone.utc)
        expires_at = get_next_expiry_time()  # Next 6 AM IST
        
        # Store OAuth tokens in Secrets Manager
        oauth_secret_arn = account.get('oauth_token_secret_arn')
        if oauth_secret_arn:
            oauth_token_data = {
                'access_token': access_token,
                'api_key': api_key,  # Store for Authorization header
                'token_expires_at': expires_at,
                'last_oauth_login': current_time.isoformat(),
                'session_valid': True,
                'client_id': client_id,
                'broker_name': 'zerodha',
                'user_id': user_id,
                'created_at': current_time.isoformat(),
                'updated_at': current_time.isoformat()
            }
            
            secretsmanager.update_secret(
                SecretId=oauth_secret_arn,
                SecretString=json.dumps(oauth_token_data)
            )
            
            # Update DynamoDB with token metadata
            table.update_item(
                Key={
                    'user_id': user_id,
                    'client_id': client_id
                },
                UpdateExpression='SET token_expires_at = :expires_at, last_oauth_login = :login_time, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':expires_at': expires_at,
                    ':login_time': current_time.isoformat(),
                    ':updated_at': current_time.isoformat()
                }
            )
            
            log_user_action(logger, user_id, "oauth_token_stored", {
                "client_id": client_id,
                "expires_at": expires_at
            })
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'data': {
                        'token_expires_at': expires_at,
                        'login_time': current_time.isoformat(),
                        'valid_until': datetime.fromisoformat(expires_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S UTC') if expires_at else 'Unknown'
                    },
                    'message': 'OAuth authentication successful'
                })
            }
            
    except Exception as e:
        logger.error("Failed to handle OAuth callback", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to handle OAuth callback',
                'message': str(e)
            })
        }

def handle_oauth_status(user_id, client_id, table, secretsmanager):
    """Check OAuth token status"""
    
    try:
        # Get broker account
        response = table.get_item(
            Key={
                'user_id': user_id,
                'client_id': client_id
            }
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Broker account not found'
                })
            }
        
        account = response['Item']
        token_expires_at = account.get('token_expires_at')
        last_oauth_login = account.get('last_oauth_login')
        
        # Check if token exists and is valid
        has_token = token_expires_at is not None and last_oauth_login is not None
        is_valid = False
        
        if has_token:
            expires_at = datetime.fromisoformat(token_expires_at.replace('Z', '+00:00'))
            is_valid = datetime.now(timezone.utc) < expires_at
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': {
                    'has_token': has_token,
                    'is_valid': is_valid,
                    'expires_at': token_expires_at,
                    'last_login': last_oauth_login,
                    'requires_login': not is_valid
                },
                'message': 'Token status retrieved successfully'
            })
        }
        
    except Exception as e:
        logger.error("Failed to check OAuth status", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to check OAuth status',
                'message': str(e)
            })
        }

def exchange_request_token_for_access_token(api_key, api_secret, request_token):
    """Exchange Zerodha request token for access token using official API"""
    
    try:
        logger.info("Starting Zerodha token exchange", extra={
            "api_key_prefix": api_key[:8] + "..." if api_key and len(api_key) > 8 else api_key,
            "request_token_prefix": request_token[:8] + "..." if request_token and len(request_token) > 8 else request_token,
            "api_secret_length": len(api_secret) if api_secret else 0
        })
        
        # Generate checksum as per Zerodha documentation
        # checksum = SHA-256(api_key + request_token + api_secret)
        checksum = hashlib.sha256(f"{api_key}{request_token}{api_secret}".encode()).hexdigest()
        
        logger.info("Generated checksum", extra={
            "checksum_prefix": checksum[:16] + "..." if checksum else None,
            "input_string_length": len(f"{api_key}{request_token}{api_secret}")
        })
        
        # Call Zerodha token exchange endpoint
        logger.info("Calling Zerodha API for token exchange")
        response = requests.post(
            "https://api.kite.trade/session/token",
            data={
                "api_key": api_key,
                "request_token": request_token,
                "checksum": checksum
            },
            timeout=30
        )
        
        logger.info("Zerodha API response received", extra={
            "status_code": response.status_code,
            "content_type": response.headers.get('content-type', 'unknown'),
            "response_length": len(response.text) if response.text else 0
        })
        
        if response.status_code != 200:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            error_message = error_data.get('message', f'HTTP {response.status_code}: {response.text}')
            logger.error("Zerodha API error", extra={"error_data": error_data, "response_text": response.text[:200]})
            raise Exception(f"Token exchange failed: {error_message}")
        
        token_data = response.json()
        logger.info("Token data parsed", extra={"status": token_data.get('status'), "has_data": bool(token_data.get('data'))})
        
        if token_data.get('status') != 'success':
            logger.error("Zerodha token exchange failed", extra={"token_data": token_data})
            raise Exception(f"Zerodha API error: {token_data.get('message', 'Unknown error')}")
        
        access_token = token_data['data']['access_token']
        logger.info("Access token extracted successfully", extra={"token_length": len(access_token) if access_token else 0})
        
        return access_token
        
    except requests.exceptions.RequestException as e:
        logger.error("Network error during token exchange", extra={"error": str(e)})
        raise Exception(f"Network error during token exchange: {str(e)}")
    except Exception as e:
        logger.error("Token exchange error", extra={"error": str(e)})
        raise Exception(f"Token exchange error: {str(e)}")

def get_next_expiry_time():
    """Calculate next 6 AM IST expiry time for Zerodha tokens"""
    
    # Get current time in UTC
    now = datetime.now(timezone.utc)
    
    # Convert to IST (UTC + 5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_now = now + ist_offset
    
    # Next 6 AM IST
    next_6am_ist = ist_now.replace(hour=6, minute=0, second=0, microsecond=0)
    
    # If it's already past 6 AM today, move to next day
    if ist_now.hour >= 6:
        next_6am_ist += timedelta(days=1)
    
    # Convert back to UTC and return ISO format
    next_6am_utc = next_6am_ist - ist_offset
    return next_6am_utc.isoformat()

def is_token_valid(token_expires_at):
    """Check if OAuth token is still valid"""
    
    if not token_expires_at:
        return False
    
    try:
        expires_at = datetime.fromisoformat(token_expires_at.replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)
        return current_time < expires_at
    except (ValueError, TypeError):
        return False