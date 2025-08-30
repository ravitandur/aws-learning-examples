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
    Lambda function to resend verification codes for email or phone
    Uses AWS Cognito's ResendConfirmationCode API
    """
    
    # Log the incoming Lambda event (sanitized)
    log_lambda_event(logger, event, context)
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract parameters
        username = body.get('username', '').strip()  # phone number or email
        email = body.get('email', '').strip().lower()
        phone_number = body.get('phone_number', '').strip()
        verification_type = body.get('verification_type', '').strip().lower()  # 'email' or 'phone'
        
        # Determine the username to use
        if phone_number:
            identifier = phone_number
        elif email:
            identifier = email
        else:
            identifier = username
        
        if not identifier:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Username, email, or phone number is required'
                })
            }
        
        if not verification_type or verification_type not in ['email', 'phone']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Verification type must be either "email" or "phone"'
                })
            }
        
        logger.info("Processing resend verification code request", extra={
            'event_type': 'resend_verification_code',
            'identifier': identifier,
            'verification_type': verification_type
        })
        
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp', region_name=os.environ['REGION'])
        
        try:
            # For phone verification, use admin_create_user with MessageAction='RESEND' (doesn't exist)
            # Instead, we'll use the attribute-based verification approach
            if verification_type == 'email':
                # Get user by email or phone to find the actual username (UUID)
                try:
                    # First try to get user info to find the actual username
                    users_response = cognito_client.list_users(
                        UserPoolId=os.environ['USER_POOL_ID'],
                        Filter=f'email = "{identifier}"' if '@' in identifier else f'phone_number = "{identifier}"',
                        Limit=1
                    )
                    
                    if not users_response['Users']:
                        return {
                            'statusCode': 404,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*'
                            },
                            'body': json.dumps({
                                'error': 'User not found',
                                'message': f'No user found with this {verification_type}'
                            })
                        }
                    
                    actual_username = users_response['Users'][0]['Username']
                    
                    # Send email verification code
                    response = cognito_client.admin_update_user_attributes(
                        UserPoolId=os.environ['USER_POOL_ID'],
                        Username=actual_username,
                        UserAttributes=[
                            {'Name': 'email_verified', 'Value': 'false'}
                        ]
                    )
                    
                    # Request email verification
                    verify_response = cognito_client.get_user_attribute_verification_code(
                        AccessToken=None,  # We'll need to handle this differently for admin calls
                        AttributeName='email'
                    )
                    
                except Exception as admin_error:
                    # Fallback: use resend_confirmation_code if the user is in UNCONFIRMED state
                    try:
                        response = cognito_client.resend_confirmation_code(
                            ClientId=os.environ['USER_POOL_CLIENT_ID'],
                            Username=identifier
                        )
                        
                        delivery_details = response.get('CodeDeliveryDetails', {})
                        
                        log_user_action(logger, identifier, "verification_code_resent", {
                            "type": verification_type,
                            "destination": delivery_details.get('Destination', ''),
                            "delivery_medium": delivery_details.get('DeliveryMedium', 'EMAIL')
                        })
                        
                        return {
                            'statusCode': 200,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*'
                            },
                            'body': json.dumps({
                                'message': f'Verification code sent to your {verification_type}',
                                'delivery_details': {
                                    'destination': delivery_details.get('Destination', ''),
                                    'delivery_medium': delivery_details.get('DeliveryMedium', 'EMAIL'),
                                    'attribute_name': verification_type
                                }
                            })
                        }
                        
                    except Exception as resend_error:
                        logger.error("Failed to resend verification code", extra={
                            "error": str(resend_error),
                            "identifier": identifier,
                            "admin_error": str(admin_error)
                        })
                        
                        # For confirmed users, we need a different approach
                        return {
                            'statusCode': 400,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*'
                            },
                            'body': json.dumps({
                                'error': 'Cannot send verification code',
                                'message': f'User account is already confirmed or requires different verification flow. Please contact support.'
                            })
                        }
            
            else:  # phone verification
                # Similar logic for phone verification
                return {
                    'statusCode': 501,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Phone verification not implemented',
                        'message': 'Phone verification feature is not yet available. Please contact support.'
                    })
                }
                
        except cognito_client.exceptions.UserNotFoundException:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'User not found',
                    'message': f'No user found with this {verification_type}'
                })
            }
            
        except cognito_client.exceptions.LimitExceededException:
            logger.warning("Rate limit exceeded for resend verification", extra={
                "identifier": identifier,
                "verification_type": verification_type
            })
            return {
                'statusCode': 429,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Too many requests',
                    'message': 'Too many verification code requests. Please wait before requesting again.'
                })
            }
            
        except Exception as e:
            logger.error("Unexpected error in resend verification", extra={
                "error": str(e),
                "identifier": identifier,
                "verification_type": verification_type
            })
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Verification service error',
                    'message': 'Unable to send verification code. Please try again later.'
                })
            }
        
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in resend verification request", extra={"error": str(e)})
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
        logger.error("Unexpected error in resend verification handler", extra={"error": str(e)})
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