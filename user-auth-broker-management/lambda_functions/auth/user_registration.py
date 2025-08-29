import json
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
import os
import sys

# Add paths for imports
sys.path.append('/opt/python')
sys.path.append('../validators')

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

# Import validators
try:
    from validators.indian_validators import validate_user_registration_data, INDIAN_STATES
except ImportError:
    # Fallback validation
    def validate_user_registration_data(user_data):
        return {"valid": True, "errors": []}
    INDIAN_STATES = []

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to handle user registration
    Validates Indian user data and creates Cognito user with DynamoDB profile
    """
    
    # Log the incoming Lambda event (sanitized)
    log_lambda_event(logger, event, context)
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract user data
        user_data = {
            'phone_number': body.get('phone_number', '').strip(),
            'email': body.get('email', '').strip().lower(),
            'full_name': body.get('full_name', '').strip(),
            'state': body.get('state', '').strip(),
            'password': body.get('password', '').strip()
        }
        
        logger.info("Processing user registration", extra={
            'event_type': 'user_registration',
            'phone_number': user_data['phone_number'],
            'email': user_data['email'],
            'state': user_data['state']
        })
        
        # Validate user data
        validation_result = validate_user_registration_data(user_data)
        if not validation_result['valid']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Validation failed',
                    'details': validation_result['errors']
                })
            }
        
        # Validate password
        if not user_data['password'] or len(user_data['password']) < 8:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Password must be at least 8 characters long'
                })
            }
        
        # Initialize AWS clients
        cognito_client = boto3.client('cognito-idp', region_name=os.environ['REGION'])
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        user_profiles_table = dynamodb.Table(os.environ['USER_PROFILES_TABLE'])
        
        # Create Cognito user
        try:
            # Check if user already exists
            try:
                cognito_client.admin_get_user(
                    UserPoolId=os.environ['USER_POOL_ID'],
                    Username=user_data['phone_number']
                )
                return {
                    'statusCode': 409,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'User already exists',
                        'message': 'A user with this phone number already exists'
                    })
                }
            except cognito_client.exceptions.UserNotFoundException:
                # User doesn't exist, proceed with creation
                pass
            
            # Create user in Cognito
            cognito_response = cognito_client.admin_create_user(
                UserPoolId=os.environ['USER_POOL_ID'],
                Username=user_data['phone_number'],
                UserAttributes=[
                    {'Name': 'email', 'Value': user_data['email']},
                    {'Name': 'phone_number', 'Value': user_data['phone_number']},
                    {'Name': 'name', 'Value': user_data['full_name']},
                    {'Name': 'custom:state', 'Value': user_data['state']},
                    {'Name': 'email_verified', 'Value': 'false'},
                    {'Name': 'phone_number_verified', 'Value': 'false'}
                ],
                MessageAction='SUPPRESS',  # Don't send welcome email
                TemporaryPassword=user_data['password']
            )
            
            user_sub = None
            for attr in cognito_response['User']['Attributes']:
                if attr['Name'] == 'sub':
                    user_sub = attr['Value']
                    break
            
            if not user_sub:
                raise Exception("Failed to get user sub from Cognito response")
            
            # Set permanent password
            cognito_client.admin_set_user_password(
                UserPoolId=os.environ['USER_POOL_ID'],
                Username=user_data['phone_number'],
                Password=user_data['password'],
                Permanent=True
            )
            
            log_user_action(logger, user_sub, "cognito_user_created", {"phone_number": user_data['phone_number']})
            
        except Exception as e:
            logger.error("Failed to create Cognito user", extra={"error": str(e), "phone_number": user_data['phone_number']})
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Failed to create user account',
                    'message': str(e)
                })
            }
        
        # Create user profile in DynamoDB
        try:
            current_time = datetime.now(timezone.utc).isoformat()
            
            user_profiles_table.put_item(
                Item={
                    'user_id': user_sub,
                    'phone_number': user_data['phone_number'],
                    'email': user_data['email'],
                    'full_name': user_data['full_name'],
                    'state': user_data['state'],
                    'created_at': current_time,
                    'updated_at': current_time,
                    'status': 'active'
                }
            )
            
            log_user_action(logger, user_sub, "profile_created", {"state": user_data['state']})
            
        except Exception as e:
            logger.error("Failed to create user profile", extra={"error": str(e), "user_id": user_sub})
            # Cleanup: delete Cognito user if DynamoDB fails
            try:
                cognito_client.admin_delete_user(
                    UserPoolId=os.environ['USER_POOL_ID'],
                    Username=user_data['phone_number']
                )
            except:
                pass
            
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Failed to create user profile',
                    'message': str(e)
                })
            }
        
        # Success response
        log_api_response(logger, 201, user_sub)
        log_user_action(logger, user_sub, "registration_completed", {
            "email": user_data['email'],
            "state": user_data['state']
        })
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'User registered successfully',
                'user_id': user_sub,
                'phone_number': user_data['phone_number'],
                'email': user_data['email'],
                'full_name': user_data['full_name'],
                'state': user_data['state'],
                'next_step': 'Please verify your email and phone number'
            })
        }
        
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in request body", extra={"error": str(e)})
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
        logger.error("Unexpected error in user registration", extra={"error": str(e)})
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