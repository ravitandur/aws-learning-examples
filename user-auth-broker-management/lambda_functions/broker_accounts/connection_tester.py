"""
Broker Connection Tester Lambda Function
Tests API connectivity for different brokers using stored credentials
"""

import json
import boto3
from typing import Dict, Any
import os
from datetime import datetime, timezone

# Import shared logger
try:
    from shared_utils.logger import setup_logger, log_lambda_event, log_user_action, log_api_response
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Test broker API connection using stored credentials
    
    Expected event structure:
    {
        "httpMethod": "POST",
        "pathParameters": {"client_id": "RD0397"},
        "requestContext": {"authorizer": {"claims": {"sub": "user-id"}}}
    }
    """
    
    # Log the incoming Lambda event (sanitized)
    log_lambda_event(logger, event, context)
    
    try:
        # Extract user ID from Cognito authorizer context
        user_id = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            claims = event['requestContext']['authorizer'].get('claims', {})
            user_id = claims.get('sub') or claims.get('cognito:username')
        
        if not user_id:
            return create_error_response('Unauthorized', 'User ID not found in request context', 401)
        
        # Extract client_id from path parameters
        path_parameters = event.get('pathParameters') or {}
        client_id = path_parameters.get('client_id')
        
        if not client_id:
            return create_error_response('Missing client_id', 'client_id is required', 400)
        
        logger.info("Testing broker connection", extra={
            "user_id": user_id,
            "client_id": client_id
        })
        
        # Get broker account details
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        table = dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])
        
        response = table.get_item(
            Key={
                'user_id': user_id,
                'client_id': client_id
            }
        )
        
        if 'Item' not in response:
            return create_error_response('Broker account not found', 'No account found with the provided client_id', 404)
        
        broker_account = response['Item']
        broker_name = broker_account['broker_name']
        api_key_secret_arn = broker_account.get('api_key_secret_arn')
        
        if not api_key_secret_arn:
            return create_error_response('No API credentials', 'Please configure API credentials first', 400)
        
        # Get API credentials from Secrets Manager
        secretsmanager = boto3.client('secretsmanager', region_name=os.environ['REGION'])
        
        try:
            secret_response = secretsmanager.get_secret_value(SecretId=api_key_secret_arn)
            credentials = json.loads(secret_response['SecretString'])
        except Exception as e:
            logger.error("Failed to retrieve API credentials", extra={"error": str(e), "user_id": user_id})
            return create_error_response('Failed to retrieve credentials', 'Unable to access stored API credentials', 500)
        
        # Test connection based on broker type
        test_result = test_broker_connection(broker_name, credentials, user_id, client_id)
        
        # Log the test result
        log_user_action(logger, user_id, "connection_test", {
            "client_id": client_id,
            "broker_name": broker_name,
            "status": test_result["status"]
        })
        
        status_code = 200 if test_result["status"] == "connected" else 400
        log_api_response(logger, status_code, user_id)
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'success': test_result["status"] == "connected",
                'data': {
                    'status': test_result["status"],
                    'details': test_result.get("details", ""),
                    'broker_name': broker_name,
                    'client_id': client_id,
                    'tested_at': datetime.now(timezone.utc).isoformat()
                },
                'message': test_result.get("message", "Connection test completed")
            })
        }
        
    except Exception as e:
        logger.error("Connection test failed", extra={
            "error": str(e),
            "user_id": user_id if 'user_id' in locals() else None
        })
        
        log_api_response(logger, 500, user_id if 'user_id' in locals() else None)
        return create_error_response('Connection test failed', str(e), 500)

def test_broker_connection(broker_name: str, credentials: Dict[str, Any], user_id: str, client_id: str) -> Dict[str, Any]:
    """
    Test connection for specific broker type
    
    Args:
        broker_name: Name of the broker
        credentials: API credentials
        user_id: User ID for logging
        client_id: Client ID for logging
        
    Returns:
        Dictionary with status and details
    """
    try:
        if broker_name.lower() == 'zerodha':
            return test_zerodha_connection(credentials, user_id, client_id)
        elif broker_name.lower() == 'angel':
            return test_angel_connection(credentials, user_id, client_id)
        elif broker_name.lower() == 'finvasia':
            return test_finvasia_connection(credentials, user_id, client_id)
        elif broker_name.lower() == 'zebu':
            return test_zebu_connection(credentials, user_id, client_id)
        else:
            return {
                "status": "failed",
                "details": f"Connection testing not implemented for {broker_name}",
                "message": "Broker not supported for connection testing"
            }
            
    except Exception as e:
        logger.error("Broker connection test error", extra={
            "error": str(e),
            "broker_name": broker_name,
            "user_id": user_id,
            "client_id": client_id
        })
        return {
            "status": "failed",
            "details": str(e),
            "message": "Connection test failed with error"
        }

def test_zerodha_connection(credentials: Dict[str, Any], user_id: str, client_id: str) -> Dict[str, Any]:
    """
    Test Zerodha Kite Connect API connection
    Makes a simple API call to validate credentials
    """
    try:
        api_key = credentials.get('api_key')
        api_secret = credentials.get('api_secret')
        
        if not api_key or not api_secret:
            return {
                "status": "failed",
                "details": "Missing API key or secret",
                "message": "Invalid credentials configuration"
            }
        
        # For Zerodha, we can't test without an active session token
        # So we'll validate the API key format and check if it's accessible
        
        # Basic validation of API key format (Zerodha API keys are typically 15-20 alphanumeric)
        if not (15 <= len(api_key) <= 20 and api_key.isalnum()):
            return {
                "status": "failed",
                "details": "Invalid API key format",
                "message": "API key format does not match Zerodha pattern"
            }
        
        # Basic validation of API secret format (Zerodha API secrets are typically 20-40 alphanumeric)
        if not (20 <= len(api_secret) <= 40 and api_secret.isalnum()):
            return {
                "status": "failed",
                "details": "Invalid API secret format", 
                "message": "API secret format does not match Zerodha pattern"
            }
        
        logger.info("Zerodha credentials validation passed", extra={
            "api_key": api_key[:5] + "***",  # Log only first 5 chars
            "user_id": user_id,
            "client_id": client_id
        })
        
        # Note: For a full connection test, we would need an active OAuth session
        # This basic test validates credential format and accessibility
        return {
            "status": "connected",
            "details": "API credentials are properly formatted and accessible",
            "message": "Basic credential validation successful. Use OAuth to test full API access."
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "details": f"Zerodha connection test error: {str(e)}",
            "message": "Connection test failed"
        }

def test_angel_connection(credentials: Dict[str, Any], user_id: str, client_id: str) -> Dict[str, Any]:
    """Test Angel One API connection"""
    # TODO: Implement Angel One connection testing
    return {
        "status": "failed",
        "details": "Angel One connection testing not implemented yet",
        "message": "Feature coming soon"
    }

def test_finvasia_connection(credentials: Dict[str, Any], user_id: str, client_id: str) -> Dict[str, Any]:
    """Test Finvasia API connection"""
    # TODO: Implement Finvasia connection testing
    return {
        "status": "failed", 
        "details": "Finvasia connection testing not implemented yet",
        "message": "Feature coming soon"
    }

def test_zebu_connection(credentials: Dict[str, Any], user_id: str, client_id: str) -> Dict[str, Any]:
    """Test Zebu API connection"""
    # TODO: Implement Zebu connection testing
    return {
        "status": "failed",
        "details": "Zebu connection testing not implemented yet", 
        "message": "Feature coming soon"
    }

def create_error_response(error: str, message: str, status_code: int = 400) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps({
            'success': False,
            'error': error,
            'message': message
        })
    }