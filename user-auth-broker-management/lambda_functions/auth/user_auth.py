import json
import boto3
import hmac
import hashlib
import base64
from typing import Dict, Any
import os

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to handle user authentication
    Authenticates user against Cognito and returns JWT tokens
    """
    
    print(f"Auth event: {json.dumps(event)}")
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract credentials
        username = body.get('username', '').strip()  # phone number or email
        password = body.get('password', '').strip()
        
        if not username or not password:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Username and password are required'
                })
            }
        
        print(f"Authentication attempt for username: {username}")
        
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp', region_name=os.environ['REGION'])
        
        try:
            # Authenticate user
            auth_response = cognito_client.admin_initiate_auth(
                UserPoolId=os.environ['USER_POOL_ID'],
                ClientId=os.environ['USER_POOL_CLIENT_ID'],
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            print(f"Authentication successful for user: {username}")
            
            # Get user details
            user_details = cognito_client.admin_get_user(
                UserPoolId=os.environ['USER_POOL_ID'],
                Username=username
            )
            
            # Extract user attributes
            user_attributes = {}
            user_sub = None
            
            for attr in user_details['UserAttributes']:
                attr_name = attr['Name']
                attr_value = attr['Value']
                
                if attr_name == 'sub':
                    user_sub = attr_value
                elif attr_name in ['email', 'phone_number', 'name']:
                    user_attributes[attr_name] = attr_value
                elif attr_name == 'custom:state':
                    user_attributes['state'] = attr_value
            
            # Prepare response
            response_data = {
                'message': 'Authentication successful',
                'user_id': user_sub,
                'user_attributes': user_attributes,
                'tokens': {
                    'access_token': auth_response['AuthenticationResult']['AccessToken'],
                    'id_token': auth_response['AuthenticationResult']['IdToken'],
                    'refresh_token': auth_response['AuthenticationResult']['RefreshToken'],
                    'token_type': auth_response['AuthenticationResult']['TokenType'],
                    'expires_in': auth_response['AuthenticationResult']['ExpiresIn']
                }
            }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(response_data)
            }
            
        except cognito_client.exceptions.NotAuthorizedException as e:
            print(f"Authentication failed for user {username}: {str(e)}")
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Authentication failed',
                    'message': 'Invalid username or password'
                })
            }
            
        except cognito_client.exceptions.UserNotFoundException as e:
            print(f"User not found: {username}")
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'User not found',
                    'message': 'No account found with this username'
                })
            }
            
        except cognito_client.exceptions.UserNotConfirmedException as e:
            print(f"User not confirmed: {username}")
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Account not verified',
                    'message': 'Please verify your email and phone number before logging in'
                })
            }
            
        except Exception as e:
            print(f"Cognito authentication error: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Authentication service error',
                    'message': str(e)
                })
            }
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
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
        print(f"Unexpected error: {str(e)}")
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