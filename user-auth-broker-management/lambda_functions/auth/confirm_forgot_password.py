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

def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password meets security requirements
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to confirm forgot password and set new password
    Uses AWS Cognito confirm_forgot_password API
    """
    
    # Log the incoming Lambda event (sanitized)
    log_lambda_event(logger, event, context)
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract required parameters
        username = body.get('username', '').strip()  # Can be email or phone
        email = body.get('email', '').strip().lower()
        confirmation_code = body.get('confirmation_code', '').strip()
        new_password = body.get('new_password', '').strip()
        
        # Use email if provided, otherwise use username
        identifier = email if email else username
        
        # Validate required fields
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
        
        if not confirmation_code:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Confirmation code is required'
                })
            }
        
        if not new_password:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'New password is required'
                })
            }
        
        # Validate password strength
        password_validation = validate_password_strength(new_password)
        if not password_validation['valid']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Password does not meet security requirements',
                    'details': password_validation['errors']
                })
            }
        
        logger.info("Processing confirm forgot password request", extra={
            'event_type': 'confirm_forgot_password_request',
            'identifier': identifier
        })
        
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp', region_name=os.environ['REGION'])
        
        try:
            # Confirm forgot password with new password
            response = cognito_client.confirm_forgot_password(
                ClientId=os.environ['USER_POOL_CLIENT_ID'],
                Username=identifier,
                ConfirmationCode=confirmation_code,
                Password=new_password
            )
            
            log_user_action(logger, identifier, "password_reset_completed", {
                "success": True
            })
            
            # Success response
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Password has been successfully reset. You can now log in with your new password.',
                    'success': True
                })
            }
            
        except cognito_client.exceptions.UserNotFoundException:
            logger.warning("Confirm forgot password attempted for non-existent user", extra={
                "identifier": identifier
            })
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'User not found',
                    'message': 'No account found with this email or username'
                })
            }
            
        except cognito_client.exceptions.CodeMismatchException:
            logger.warning("Invalid confirmation code provided", extra={
                "identifier": identifier
            })
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid confirmation code',
                    'message': 'The confirmation code is incorrect or has expired'
                })
            }
            
        except cognito_client.exceptions.ExpiredCodeException:
            logger.warning("Expired confirmation code provided", extra={
                "identifier": identifier
            })
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Confirmation code expired',
                    'message': 'The confirmation code has expired. Please request a new password reset.'
                })
            }
            
        except cognito_client.exceptions.InvalidPasswordException as e:
            logger.warning("Invalid password provided", extra={
                "identifier": identifier,
                "error": str(e)
            })
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid password',
                    'message': 'Password does not meet the security requirements'
                })
            }
            
        except cognito_client.exceptions.LimitExceededException:
            logger.warning("Rate limit exceeded for confirm forgot password", extra={
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
                    'message': 'Too many password reset attempts. Please try again later.'
                })
            }
            
        except cognito_client.exceptions.InvalidParameterException as e:
            logger.error("Invalid parameter in confirm forgot password", extra={
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
            
        except Exception as e:
            logger.error("Unexpected error in confirm forgot password", extra={
                "error": str(e),
                "identifier": identifier
            })
            log_user_action(logger, identifier, "password_reset_failed", {
                "error": str(e)
            })
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Password reset service error',
                    'message': 'Unable to complete password reset. Please try again later.'
                })
            }
        
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in confirm forgot password request", extra={"error": str(e)})
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
        logger.error("Unexpected error in confirm forgot password handler", extra={"error": str(e)})
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