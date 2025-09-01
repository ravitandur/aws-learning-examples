"""
Refactored OAuth Handler using Strategy Pattern
Multi-broker OAuth handler that routes requests to appropriate broker strategies
"""

import json
from typing import Dict, Any
import os
from datetime import datetime, timezone

# Import shared logger
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
        logger.info("Lambda invocation started")
        
    def log_user_action(logger, user_id, action, details=None):
        logger.info(f"User {user_id} performed action: {action}")
        
    def log_api_response(logger, status_code, user_id=None, response_size=None):
        logger.info(f"API response: {status_code}")

from oauth_factory import get_oauth_factory, route_oauth_request

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Multi-broker OAuth Lambda handler using strategy pattern
    
    Supports endpoints:
    - POST /broker-accounts/{client_id}/oauth/login
    - POST /broker-accounts/{client_id}/oauth/callback  
    - GET  /broker-accounts/{client_id}/oauth/status
    
    Automatically detects broker type from broker account and routes to appropriate handler
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
            response = create_error_response(
                'Unauthorized',
                'User ID not found in request context',
                401
            )
            log_api_response(logger, 401)
            return response
        
        # Extract request parameters
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        client_id = path_parameters.get('client_id')
        oauth_action = path_parameters.get('oauth_action')  # login, callback, status
        
        # Validate required parameters
        if not client_id:
            response = create_error_response(
                'Missing client_id',
                'client_id is required for OAuth operations',
                400
            )
            log_api_response(logger, 400, user_id)
            return response
        
        if not oauth_action:
            response = create_error_response(
                'Missing oauth_action',
                'OAuth action (login/callback/status) is required',
                400
            )
            log_api_response(logger, 400, user_id)
            return response
        
        logger.info("Processing multi-broker OAuth request", extra={
            "user_id": user_id,
            "client_id": client_id,
            "oauth_action": oauth_action,
            "http_method": http_method
        })
        
        # Validate HTTP method for action
        valid_methods = {
            'login': ['POST'],
            'callback': ['POST'], 
            'status': ['GET']
        }
        
        if oauth_action not in valid_methods:
            response = create_error_response(
                'Invalid OAuth action',
                f'OAuth action {oauth_action} is not supported',
                400
            )
            log_api_response(logger, 400, user_id)
            return response
        
        if http_method not in valid_methods[oauth_action]:
            response = create_error_response(
                'Method not allowed',
                f'Method {http_method} not allowed for action {oauth_action}',
                405
            )
            log_api_response(logger, 405, user_id)
            return response
        
        # Get broker name from broker account (auto-detection)
        broker_name = get_broker_name_for_account(user_id, client_id)
        if not broker_name:
            response = create_error_response(
                'Broker account not found',
                f'No broker account found with client_id: {client_id}',
                404
            )
            log_api_response(logger, 404, user_id)
            return response
        
        # Parse callback parameters for callback action
        callback_params = {}
        if oauth_action == 'callback':
            callback_params = parse_callback_params(event)
        
        # Route request to appropriate broker handler using factory
        logger.info("Routing OAuth request", extra={
            "broker_name": broker_name,
            "oauth_action": oauth_action,
            "user_id": user_id,
            "client_id": client_id
        })
        
        response = route_oauth_request(
            broker_name=broker_name,
            action=oauth_action,
            user_id=user_id,
            client_id=client_id,
            callback_params=callback_params
        )
        
        # Log successful operation
        status_code = response.get('statusCode', 500)
        log_api_response(logger, status_code, user_id)
        
        if status_code == 200:
            log_user_action(logger, user_id, f"oauth_{oauth_action}_success", {
                "broker_name": broker_name,
                "client_id": client_id
            })
        
        return response
        
    except Exception as e:
        logger.error("Unexpected error in multi-broker OAuth handler", extra={
            "error": str(e),
            "user_id": user_id if 'user_id' in locals() else None
        })
        
        response = create_error_response(
            'Internal server error',
            'An unexpected error occurred while processing OAuth request',
            500
        )
        log_api_response(logger, 500, user_id if 'user_id' in locals() else None)
        return response

def get_broker_name_for_account(user_id: str, client_id: str) -> str:
    """
    Get broker name for the specified broker account
    
    Args:
        user_id: User ID
        client_id: Client ID
        
    Returns:
        Broker name or None if account not found
    """
    try:
        import boto3
        
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        table = dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])
        
        response = table.get_item(
            Key={
                'user_id': user_id,
                'client_id': client_id
            }
        )
        
        if 'Item' in response:
            return response['Item']['broker_name']
        
        return None
        
    except Exception as e:
        logger.error("Failed to get broker name", extra={
            "error": str(e),
            "user_id": user_id,
            "client_id": client_id
        })
        return None

def parse_callback_params(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse OAuth callback parameters from request
    
    Args:
        event: Lambda event
        
    Returns:
        Dictionary of callback parameters
    """
    try:
        # Try to parse JSON body
        if event.get('body'):
            if isinstance(event['body'], str):
                return json.loads(event['body'])
            else:
                return event['body']
        
        # Fallback to query parameters
        query_params = event.get('queryStringParameters') or {}
        return query_params
        
    except json.JSONDecodeError:
        logger.warning("Failed to parse callback parameters")
        return {}
    except Exception as e:
        logger.error("Error parsing callback parameters", extra={"error": str(e)})
        return {}

def create_error_response(error: str, message: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Create standardized error response
    
    Args:
        error: Error type
        message: Error message
        status_code: HTTP status code
        
    Returns:
        HTTP response dictionary
    """
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

def create_success_response(data: Dict[str, Any], message: str = "Success", 
                          status_code: int = 200) -> Dict[str, Any]:
    """
    Create standardized success response
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        HTTP response dictionary
    """
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

# Additional utility functions for OAuth operations

def get_supported_brokers() -> Dict[str, Any]:
    """
    Get list of brokers with OAuth support
    
    Returns:
        Dictionary with supported brokers and their capabilities
    """
    try:
        factory = get_oauth_factory()
        supported_brokers = factory.get_supported_brokers()
        
        broker_info = {}
        for broker_name in supported_brokers:
            capabilities = factory.get_broker_capabilities(broker_name)
            broker_info[broker_name] = capabilities
        
        return {
            'supported_brokers': supported_brokers,
            'broker_capabilities': broker_info
        }
        
    except Exception as e:
        logger.error("Failed to get supported brokers", extra={"error": str(e)})
        return {
            'supported_brokers': [],
            'broker_capabilities': {}
        }

def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for OAuth service
    
    Returns:
        Health status response
    """
    try:
        factory = get_oauth_factory()
        supported_brokers = factory.get_supported_brokers()
        
        return create_success_response({
            'service': 'Multi-broker OAuth Handler',
            'status': 'healthy',
            'supported_brokers': supported_brokers,
            'total_brokers': len(supported_brokers),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, 'OAuth service is healthy')
        
    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e)})
        return create_error_response(
            'Health check failed',
            str(e),
            503
        )

# For debugging and monitoring
def get_oauth_statistics(user_id: str = None) -> Dict[str, Any]:
    """
    Get OAuth usage statistics
    
    Args:
        user_id: Optional user ID for user-specific stats
        
    Returns:
        OAuth statistics
    """
    try:
        # This could be expanded to include actual usage metrics
        factory = get_oauth_factory()
        
        stats = {
            'total_supported_brokers': len(factory.get_supported_brokers()),
            'supported_brokers': factory.get_supported_brokers(),
            'service_version': '2.0.0',  # Multi-broker version
            'architecture': 'Strategy Pattern with Factory Routing'
        }
        
        if user_id:
            # Add user-specific stats if needed
            stats['user_id'] = user_id
            # TODO: Add user-specific OAuth usage metrics
        
        return create_success_response(stats, 'OAuth statistics retrieved')
        
    except Exception as e:
        logger.error("Failed to get OAuth statistics", extra={"error": str(e)})
        return create_error_response(
            'Failed to get statistics',
            str(e),
            500
        )