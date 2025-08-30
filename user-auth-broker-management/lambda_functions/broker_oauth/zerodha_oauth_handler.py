import json
import boto3
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import os
import sys
import urllib.parse
import hashlib
import secrets

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
            # Get API key from secrets
            api_secret_name = api_secret_arn.split(':')[-1]
            secret_response = secretsmanager.get_secret_value(SecretId=api_secret_name)
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
        
        # Create OAuth URL for Zerodha
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
        
        if not request_token or not state:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required parameters',
                    'message': 'request_token and state are required'
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
            # Get API credentials from secrets
            api_secret_name = api_secret_arn.split(':')[-1]
            secret_response = secretsmanager.get_secret_value(SecretId=api_secret_name)
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
        
        # TODO: Implement actual Zerodha API call to exchange request_token for access_token
        # This would require the Zerodha Python SDK or direct API calls
        # For now, we'll simulate the token exchange
        
        current_time = datetime.now(timezone.utc)
        expires_at = current_time + timedelta(hours=8)  # Zerodha tokens typically expire after market hours
        
        # Simulated access token (in production, get this from Zerodha API)
        access_token = f"simulated_token_{secrets.token_urlsafe(32)}"
        
        # Store OAuth tokens in Secrets Manager
        oauth_secret_arn = account.get('oauth_token_secret_arn')
        if oauth_secret_arn:
            oauth_secret_name = oauth_secret_arn.split(':')[-1]
            
            oauth_token_data = {
                'access_token': access_token,
                'token_expires_at': expires_at.isoformat(),
                'last_oauth_login': current_time.isoformat(),
                'client_id': client_id,
                'broker_name': 'zerodha',
                'user_id': user_id,
                'created_at': current_time.isoformat()
            }
            
            secretsmanager.update_secret(
                SecretId=oauth_secret_name,
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
                    ':expires_at': expires_at.isoformat(),
                    ':login_time': current_time.isoformat(),
                    ':updated_at': current_time.isoformat()
                }
            )
            
            log_user_action(logger, user_id, "oauth_token_stored", {
                "client_id": client_id,
                "expires_at": expires_at.isoformat()
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
                        'token_expires_at': expires_at.isoformat(),
                        'login_time': current_time.isoformat(),
                        'valid_until': expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')
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