"""
WebSocket $default Route Handler
Handles incoming messages from clients (subscriptions, heartbeats, etc.)
"""

import json
import os
import logging
from typing import Any, Dict, List

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ.get('WEBSOCKET_CONNECTIONS_TABLE', ''))

# Valid subscription channels
VALID_CHANNELS = {'orders', 'positions', 'pnl', 'executions', 'all'}


def get_api_gateway_client(event: Dict[str, Any]) -> Any:
    """Create API Gateway Management client from event context."""
    domain = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    endpoint_url = f"https://{domain}/{stage}"

    return boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=endpoint_url
    )


def send_message(client: Any, connection_id: str, message: Dict[str, Any]) -> bool:
    """Send a message to a specific connection."""
    try:
        client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message).encode('utf-8')
        )
        return True
    except client.exceptions.GoneException:
        # Connection is stale, remove it
        logger.info(f"Removing stale connection: {connection_id}")
        try:
            connections_table.delete_item(Key={'connection_id': connection_id})
        except Exception:
            pass
        return False
    except Exception as e:
        logger.error(f"Error sending message to {connection_id}: {e}")
        return False


def handle_subscribe(connection_id: str, channels: List[str]) -> Dict[str, Any]:
    """Handle subscription request."""
    # Validate channels
    valid_channels = [ch for ch in channels if ch in VALID_CHANNELS]
    invalid_channels = [ch for ch in channels if ch not in VALID_CHANNELS]

    if not valid_channels:
        return {
            'type': 'error',
            'message': f'Invalid channels: {invalid_channels}. Valid channels: {list(VALID_CHANNELS)}'
        }

    # Update subscriptions in DynamoDB
    try:
        # Get current subscriptions
        response = connections_table.get_item(Key={'connection_id': connection_id})
        current = response.get('Item', {}).get('subscriptions', [])

        # Merge subscriptions
        if 'all' in valid_channels:
            new_subs = list(VALID_CHANNELS - {'all'})
        else:
            new_subs = list(set(current) | set(valid_channels))

        connections_table.update_item(
            Key={'connection_id': connection_id},
            UpdateExpression='SET subscriptions = :subs',
            ExpressionAttributeValues={':subs': new_subs}
        )

        return {
            'type': 'subscribed',
            'channels': new_subs,
            'message': f'Subscribed to {len(new_subs)} channel(s)'
        }

    except Exception as e:
        logger.error(f"Error updating subscriptions: {e}")
        return {
            'type': 'error',
            'message': f'Failed to subscribe: {str(e)}'
        }


def handle_unsubscribe(connection_id: str, channels: List[str]) -> Dict[str, Any]:
    """Handle unsubscription request."""
    try:
        # Get current subscriptions
        response = connections_table.get_item(Key={'connection_id': connection_id})
        current = set(response.get('Item', {}).get('subscriptions', []))

        # Remove specified channels
        if 'all' in channels:
            new_subs = []
        else:
            new_subs = list(current - set(channels))

        connections_table.update_item(
            Key={'connection_id': connection_id},
            UpdateExpression='SET subscriptions = :subs',
            ExpressionAttributeValues={':subs': new_subs}
        )

        return {
            'type': 'unsubscribed',
            'channels': new_subs,
            'message': f'Now subscribed to {len(new_subs)} channel(s)'
        }

    except Exception as e:
        logger.error(f"Error updating subscriptions: {e}")
        return {
            'type': 'error',
            'message': f'Failed to unsubscribe: {str(e)}'
        }


def handle_ping() -> Dict[str, Any]:
    """Handle heartbeat ping."""
    return {
        'type': 'pong',
        'timestamp': int(__import__('time').time() * 1000)
    }


def handle_get_status(connection_id: str) -> Dict[str, Any]:
    """Return current connection status."""
    try:
        response = connections_table.get_item(Key={'connection_id': connection_id})
        item = response.get('Item', {})

        return {
            'type': 'status',
            'connection_id': connection_id,
            'user_id': item.get('user_id'),
            'subscriptions': item.get('subscriptions', []),
            'connected_at': item.get('connected_at')
        }

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            'type': 'error',
            'message': f'Failed to get status: {str(e)}'
        }


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket $default route.
    Processes client messages for subscriptions, heartbeats, etc.

    Message Types:
    - { "action": "subscribe", "channels": ["orders", "positions"] }
    - { "action": "unsubscribe", "channels": ["orders"] }
    - { "action": "ping" }
    - { "action": "status" }
    """
    logger.info(f"Message event: {json.dumps(event)}")

    connection_id = event['requestContext']['connectionId']

    # Parse message body
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        body = {}

    action = body.get('action', '').lower()

    # Process action
    if action == 'subscribe':
        channels = body.get('channels', body.get('channel', []))
        if isinstance(channels, str):
            channels = [channels]
        response = handle_subscribe(connection_id, channels)

    elif action == 'unsubscribe':
        channels = body.get('channels', body.get('channel', []))
        if isinstance(channels, str):
            channels = [channels]
        response = handle_unsubscribe(connection_id, channels)

    elif action == 'ping':
        response = handle_ping()

    elif action == 'status':
        response = handle_get_status(connection_id)

    else:
        response = {
            'type': 'error',
            'message': f'Unknown action: {action}. Valid actions: subscribe, unsubscribe, ping, status'
        }

    # Send response back to client
    api_client = get_api_gateway_client(event)
    send_message(api_client, connection_id, response)

    return {
        'statusCode': 200,
        'body': 'Message processed'
    }
