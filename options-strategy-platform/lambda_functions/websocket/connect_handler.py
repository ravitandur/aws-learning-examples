"""
WebSocket $connect Route Handler
Handles new WebSocket connections and stores connection info in DynamoDB
"""

import json
import os
import time
import logging
from typing import Any, Dict

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ.get('WEBSOCKET_CONNECTIONS_TABLE', ''))

# TTL for connections (24 hours)
CONNECTION_TTL_SECONDS = 86400


def extract_user_id_from_token(token: str) -> str | None:
    """
    Extract user_id from JWT token.
    In production, this should verify the token signature.
    """
    try:
        import base64
        # JWT format: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None

        # Decode payload (add padding if needed)
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding

        decoded = base64.b64decode(payload)
        payload_data = json.loads(decoded)

        # Cognito uses 'sub' for user ID
        return payload_data.get('sub') or payload_data.get('user_id')
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        return None


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket $connect route.
    Stores connection info in DynamoDB with TTL.

    Connection can include:
    - Authorization header with JWT token
    - Query string parameters for auth
    """
    logger.info(f"Connect event: {json.dumps(event)}")

    connection_id = event['requestContext']['connectionId']

    # Extract user_id from authorization
    user_id = None

    # Try Authorization header first
    headers = event.get('headers', {}) or {}
    auth_header = headers.get('Authorization') or headers.get('authorization')

    if auth_header:
        token = auth_header.replace('Bearer ', '').strip()
        user_id = extract_user_id_from_token(token)

    # Try query string parameters as fallback
    if not user_id:
        query_params = event.get('queryStringParameters', {}) or {}
        token = query_params.get('token')
        if token:
            user_id = extract_user_id_from_token(token)
        else:
            user_id = query_params.get('user_id')

    # If no user_id, reject connection
    if not user_id:
        logger.warning(f"Connection {connection_id} rejected: No valid user_id")
        return {
            'statusCode': 401,
            'body': 'Unauthorized: No valid authentication provided'
        }

    # Store connection in DynamoDB
    try:
        current_time = int(time.time())
        ttl = current_time + CONNECTION_TTL_SECONDS

        connections_table.put_item(
            Item={
                'connection_id': connection_id,
                'user_id': user_id,
                'connected_at': current_time,
                'subscriptions': [],  # Will be populated via message handler
                'ttl': ttl,
            }
        )

        logger.info(f"Connection {connection_id} stored for user {user_id}")

        return {
            'statusCode': 200,
            'body': 'Connected'
        }

    except Exception as e:
        logger.error(f"Error storing connection: {e}")
        return {
            'statusCode': 500,
            'body': f'Failed to store connection: {str(e)}'
        }
