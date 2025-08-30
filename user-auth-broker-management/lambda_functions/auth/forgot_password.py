import json
import boto3
from typing import Dict, Any
import os
import sys

# Add paths for imports
sys.path.append('/opt/python')
sys.path.append('../validators')

# Import shared logger (copied during deployment)
try:
    from shared_utils.logger import setup_logger, log_lambda_event, log_user_action, log_api_response
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
    Lambda function to handle forgot password requests
    Initiates password reset flow using AWS Cognito
    """
    
    # Log the incoming Lambda event (sanitized)
    log_lambda_event(logger, event, context)
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract email/username
        username = body.get('username', '').strip()  # Can be email or phone
        email = body.get('email', '').strip().lower()
        
        # Use email if provided, otherwise use username
        identifier = email if email else username
        
        if not identifier:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Email or username is required'
                })
            }
        
        logger.info("Processing forgot password request", extra={
            'event_type': 'forgot_password_request',
            'identifier': identifier
        })
        
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp', region_name=os.environ['REGION'])
        
        try:
            # Initiate forgot password flow
            response = cognito_client.forgot_password(
                ClientId=os.environ['USER_POOL_CLIENT_ID'],
                Username=identifier
            )
            
            # Extract delivery details
            code_delivery_details = response.get('CodeDeliveryDetails', {})
            destination = code_delivery_details.get('Destination', '')
            delivery_medium = code_delivery_details.get('DeliveryMedium', 'EMAIL')
            
            log_user_action(logger, identifier, "forgot_password_initiated", {
                "delivery_medium": delivery_medium,
                "destination_masked": destination
            })
            
            # Success response (don't reveal if user exists for security)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'If an account with that email exists, a verification code has been sent.',
                    'delivery_details': {
                        'destination': destination,
                        'delivery_medium': delivery_medium
                    }
                })
            }
            
        except cognito_client.exceptions.UserNotFoundException:
            # Don't reveal that user doesn't exist for security
            logger.info(f"Forgot password attempted for non-existent user: {identifier}")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'If an account with that email exists, a verification code has been sent.'
                })
            }
            
        except cognito_client.exceptions.InvalidParameterException as e:
            logger.error("Invalid parameter in forgot password request", extra={
                "error": str(e),
                "identifier": identifier
            })
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid request parameters',
                    'message': str(e)
                })
            }
            
        except cognito_client.exceptions.LimitExceededException:
            logger.warning("Rate limit exceeded for forgot password", extra={
                "identifier": identifier
            })
            return {
                'statusCode': 429,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Too many requests',
                    'message': 'Too many forgot password attempts. Please try again later.'
                })
            }
            
        except Exception as e:
            logger.error("Unexpected error in forgot password", extra={
                "error": str(e),
                "identifier": identifier
            })
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Password reset service error',
                    'message': 'Unable to process forgot password request. Please try again later.'
                })
            }
        
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in forgot password request", extra={"error": str(e)})
        log_api_response(logger, 400)
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid JSON in request body'
            })
        }
        
    except Exception as e:
        logger.error("Unexpected error in forgot password handler", extra={"error": str(e)})
        log_api_response(logger, 500)
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