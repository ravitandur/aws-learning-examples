import json
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
import os
import sys

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
    Lambda function to manage broker accounts for authenticated users
    Handles CRUD operations for broker account data and credentials
    """
    
    # Log the incoming Lambda event (sanitized - this will redact sensitive data)
    log_lambda_event(logger, event, context)
    
    try:
        # Get user ID from Cognito authorizer context
        user_id = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            # API Gateway Cognito authorizer adds user info to context
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
        
        logger.info("Processing broker account request", extra={"user_id": user_id, "http_method": http_method})
        path_parameters = event.get('pathParameters') or {}
        broker_account_id = path_parameters.get('broker_account_id')
        
        # Initialize AWS clients
        dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
        secretsmanager = boto3.client('secretsmanager', region_name=os.environ['REGION'])
        broker_accounts_table = dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])
        
        # Route based on HTTP method
        if http_method == 'POST':
            return handle_create_broker_account(event, user_id, broker_accounts_table, secretsmanager)
        elif http_method == 'GET':
            return handle_get_broker_accounts(event, user_id, broker_accounts_table)
        elif http_method == 'PUT' and broker_account_id:
            return handle_update_broker_account(event, user_id, broker_account_id, broker_accounts_table, secretsmanager)
        elif http_method == 'DELETE' and broker_account_id:
            return handle_delete_broker_account(event, user_id, broker_account_id, broker_accounts_table, secretsmanager)
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Method not allowed'
                })
            }
            
    except Exception as e:
        logger.error("Unexpected error in broker account handler", extra={"error": str(e)})
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

def handle_create_broker_account(event, user_id, table, secretsmanager):
    """Create a new broker account for the user"""
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Extract broker account data
        broker_name = body.get('broker_name', '').strip().lower()
        api_key = body.get('api_key', '').strip()
        api_secret = body.get('api_secret', '').strip()
        account_type = body.get('account_type', 'trading').strip().lower()
        
        # Validate required fields
        if not broker_name or not api_key or not api_secret:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required fields',
                    'message': 'broker_name, api_key, and api_secret are required'
                })
            }
        
        # Validate broker name (currently supporting Zerodha)
        supported_brokers = ['zerodha']
        if broker_name not in supported_brokers:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Unsupported broker',
                    'message': f'Currently supported brokers: {", ".join(supported_brokers)}'
                })
            }
        
        # Generate unique broker account ID
        broker_account_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Store API credentials in Secrets Manager with environment-specific naming
        company_prefix = os.environ.get('COMPANY_PREFIX', 'ql')
        environment = os.environ.get('ENVIRONMENT', 'dev')
        secret_name = f"{company_prefix}-zerodha-credentials-{environment}-{user_id}-{broker_account_id}"
        
        try:
            secret_response = secretsmanager.create_secret(
                Name=secret_name,
                Description=f"Zerodha API credentials for user {user_id}",
                SecretString=json.dumps({
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'broker_name': broker_name,
                    'user_id': user_id,
                    'created_at': current_time
                })
            )
            
            secret_arn = secret_response['ARN']
            log_user_action(logger, user_id, "broker_credentials_stored", {"broker_name": broker_name})
            
        except Exception as e:
            logger.error("Failed to store credentials in Secrets Manager", extra={"error": str(e), "user_id": user_id})
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Failed to store credentials securely',
                    'message': str(e)
                })
            }
        
        # Store broker account in DynamoDB
        try:
            broker_account_item = {
                'user_id': user_id,
                'broker_account_id': broker_account_id,
                'broker_name': broker_name,
                'account_type': account_type,
                'api_key_secret_arn': secret_arn,
                'account_status': 'active',
                'created_at': current_time,
                'updated_at': current_time,
                'metadata': {
                    'exchanges_enabled': ['NSE', 'BSE'],  # Default for Zerodha
                    'products_enabled': ['MIS', 'CNC', 'NRML']
                }
            }
            
            table.put_item(Item=broker_account_item)
            
            log_user_action(logger, user_id, "broker_account_created", {"broker_name": broker_name, "account_type": account_type})
            
            # Return response without sensitive data
            response_item = {k: v for k, v in broker_account_item.items() 
                           if k not in ['api_key_secret_arn']}
            response_item['has_credentials'] = True
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'data': response_item,
                    'message': 'Broker account created successfully'
                })
            }
            
        except Exception as e:
            # Cleanup: delete the secret if DynamoDB fails
            try:
                secretsmanager.delete_secret(
                    SecretId=secret_name,
                    ForceDeleteWithoutRecovery=True
                )
            except:
                pass
                
            logger.error("Failed to create broker account record", extra={"error": str(e), "user_id": user_id})
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Failed to create broker account',
                    'message': str(e)
                })
            }
        
    except json.JSONDecodeError:
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

def handle_get_broker_accounts(event, user_id, table):
    """Get all broker accounts for the user"""
    
    try:
        # Query broker accounts for the user
        response = table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={
                ':user_id': user_id
            }
        )
        
        # Remove sensitive data from response
        broker_accounts = []
        for item in response['Items']:
            account = {k: v for k, v in item.items() 
                      if k not in ['api_key_secret_arn']}
            account['has_credentials'] = 'api_key_secret_arn' in item
            broker_accounts.append(account)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': broker_accounts,
                'message': f'Retrieved {len(broker_accounts)} broker accounts'
            })
        }
        
    except Exception as e:
        logger.error("Failed to retrieve broker accounts", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve broker accounts',
                'message': str(e)
            })
        }

def handle_update_broker_account(event, user_id, broker_account_id, table, secretsmanager):
    """Update an existing broker account"""
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Get existing broker account
        response = table.get_item(
            Key={
                'user_id': user_id,
                'broker_account_id': broker_account_id
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
        
        existing_account = response['Item']
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Update fields that are provided
        update_expression_parts = []
        expression_attribute_values = {}
        
        if 'account_status' in body:
            update_expression_parts.append('account_status = :status')
            expression_attribute_values[':status'] = body['account_status']
        
        # Update credentials if provided
        if 'api_key' in body or 'api_secret' in body:
            # Get existing credentials
            secret_arn = existing_account.get('api_key_secret_arn')
            if secret_arn:
                try:
                    secret_name = secret_arn.split(':')[-1]
                    existing_secret = secretsmanager.get_secret_value(SecretId=secret_name)
                    existing_creds = json.loads(existing_secret['SecretString'])
                    
                    # Update credentials
                    new_creds = existing_creds.copy()
                    if 'api_key' in body:
                        new_creds['api_key'] = body['api_key']
                    if 'api_secret' in body:
                        new_creds['api_secret'] = body['api_secret']
                    new_creds['updated_at'] = current_time
                    
                    # Update secret
                    secretsmanager.update_secret(
                        SecretId=secret_name,
                        SecretString=json.dumps(new_creds)
                    )
                    
                except Exception as e:
                    logger.error("Failed to update credentials in Secrets Manager", extra={"error": str(e), "user_id": user_id})
                    return {
                        'statusCode': 500,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'error': 'Failed to update credentials',
                            'message': str(e)
                        })
                    }
        
        # Always update the updated_at timestamp
        update_expression_parts.append('updated_at = :updated_at')
        expression_attribute_values[':updated_at'] = current_time
        
        if update_expression_parts:
            # Update the item in DynamoDB
            table.update_item(
                Key={
                    'user_id': user_id,
                    'broker_account_id': broker_account_id
                },
                UpdateExpression='SET ' + ', '.join(update_expression_parts),
                ExpressionAttributeValues=expression_attribute_values
            )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Broker account updated successfully',
                'broker_account_id': broker_account_id
            })
        }
        
    except json.JSONDecodeError:
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
        logger.error("Failed to update broker account", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to update broker account',
                'message': str(e)
            })
        }

def handle_delete_broker_account(event, user_id, broker_account_id, table, secretsmanager):
    """Delete a broker account and its credentials"""
    
    try:
        # Get existing broker account
        response = table.get_item(
            Key={
                'user_id': user_id,
                'broker_account_id': broker_account_id
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
        
        existing_account = response['Item']
        
        # Delete credentials from Secrets Manager
        secret_arn = existing_account.get('api_key_secret_arn')
        if secret_arn:
            try:
                secret_name = secret_arn.split(':')[-1]
                secretsmanager.delete_secret(
                    SecretId=secret_name,
                    ForceDeleteWithoutRecovery=True
                )
                log_user_action(logger, user_id, "broker_credentials_deleted", {"secret_name": secret_name})
            except Exception as e:
                logger.error("Failed to delete secret", extra={"error": str(e), "user_id": user_id})
                # Continue with DynamoDB deletion even if secret deletion fails
        
        # Delete from DynamoDB
        table.delete_item(
            Key={
                'user_id': user_id,
                'broker_account_id': broker_account_id
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Broker account deleted successfully',
                'broker_account_id': broker_account_id
            })
        }
        
    except Exception as e:
        logger.error("Failed to delete broker account", extra={"error": str(e), "user_id": user_id})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to delete broker account',
                'message': str(e)
            })
        }