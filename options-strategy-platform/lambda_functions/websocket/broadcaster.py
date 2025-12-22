"""
WebSocket Broadcaster
Utility for broadcasting messages to connected clients based on subscriptions
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class WebSocketBroadcaster:
    """
    Broadcasts messages to WebSocket clients based on their subscriptions.

    Usage:
        broadcaster = WebSocketBroadcaster(
            connections_table_name='my-connections-table',
            endpoint_url='https://xxx.execute-api.region.amazonaws.com/stage'
        )
        broadcaster.broadcast_order_update(user_id, order_data)
    """

    def __init__(
        self,
        connections_table_name: Optional[str] = None,
        endpoint_url: Optional[str] = None
    ):
        """
        Initialize broadcaster.

        Args:
            connections_table_name: DynamoDB table name (uses env var if not provided)
            endpoint_url: WebSocket API endpoint (uses env var if not provided)
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = connections_table_name or os.environ.get('WEBSOCKET_CONNECTIONS_TABLE', '')
        self.connections_table = self.dynamodb.Table(self.table_name)

        self.endpoint_url = endpoint_url or os.environ.get('WEBSOCKET_ENDPOINT_URL', '')
        self.api_client = None

        if self.endpoint_url:
            self.api_client = boto3.client(
                'apigatewaymanagementapi',
                endpoint_url=self.endpoint_url
            )

    def _get_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all connections for a user from DynamoDB."""
        try:
            response = self.connections_table.query(
                IndexName='ConnectionsByUser',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error querying connections for user {user_id}: {e}")
            return []

    def _send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific connection."""
        if not self.api_client:
            logger.warning("No API client configured for WebSocket broadcasting")
            return False

        try:
            self.api_client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(message).encode('utf-8')
            )
            return True
        except self.api_client.exceptions.GoneException:
            # Connection is stale, remove it
            logger.info(f"Removing stale connection: {connection_id}")
            self._remove_stale_connection(connection_id)
            return False
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            return False

    def _remove_stale_connection(self, connection_id: str) -> None:
        """Remove a stale connection from DynamoDB."""
        try:
            self.connections_table.delete_item(Key={'connection_id': connection_id})
        except Exception as e:
            logger.error(f"Error removing stale connection: {e}")

    def broadcast_to_user(
        self,
        user_id: str,
        channel: str,
        message_type: str,
        data: Dict[str, Any]
    ) -> int:
        """
        Broadcast a message to all connections of a user subscribed to a channel.

        Args:
            user_id: The user ID to broadcast to
            channel: The channel name (orders, positions, pnl, executions)
            message_type: The message type identifier
            data: The message payload

        Returns:
            Number of successful deliveries
        """
        connections = self._get_user_connections(user_id)
        successful = 0

        message = {
            'type': message_type,
            'channel': channel,
            'data': data,
            'timestamp': int(__import__('time').time() * 1000)
        }

        for conn in connections:
            subscriptions = conn.get('subscriptions', [])

            # Check if connection is subscribed to this channel
            if channel in subscriptions or 'all' in subscriptions:
                if self._send_to_connection(conn['connection_id'], message):
                    successful += 1

        logger.info(f"Broadcast to user {user_id}: {successful}/{len(connections)} delivered")
        return successful

    def broadcast_order_update(self, user_id: str, order: Dict[str, Any]) -> int:
        """Broadcast an order update to subscribed clients."""
        return self.broadcast_to_user(
            user_id=user_id,
            channel='orders',
            message_type='order_update',
            data=order
        )

    def broadcast_position_update(self, user_id: str, position: Dict[str, Any]) -> int:
        """Broadcast a position update to subscribed clients."""
        return self.broadcast_to_user(
            user_id=user_id,
            channel='positions',
            message_type='position_update',
            data=position
        )

    def broadcast_pnl_update(self, user_id: str, pnl_data: Dict[str, Any]) -> int:
        """Broadcast a P&L update to subscribed clients."""
        return self.broadcast_to_user(
            user_id=user_id,
            channel='pnl',
            message_type='pnl_update',
            data=pnl_data
        )

    def broadcast_execution_update(self, user_id: str, execution: Dict[str, Any]) -> int:
        """Broadcast an execution update to subscribed clients."""
        return self.broadcast_to_user(
            user_id=user_id,
            channel='executions',
            message_type='execution_update',
            data=execution
        )

    def broadcast_to_all_user_connections(
        self,
        user_id: str,
        message_type: str,
        data: Dict[str, Any]
    ) -> int:
        """
        Broadcast to all connections of a user regardless of subscriptions.
        Useful for system messages, alerts, etc.
        """
        connections = self._get_user_connections(user_id)
        successful = 0

        message = {
            'type': message_type,
            'data': data,
            'timestamp': int(__import__('time').time() * 1000)
        }

        for conn in connections:
            if self._send_to_connection(conn['connection_id'], message):
                successful += 1

        return successful


# Singleton instance for easy import
_broadcaster_instance: Optional[WebSocketBroadcaster] = None


def get_broadcaster() -> WebSocketBroadcaster:
    """Get or create the singleton broadcaster instance."""
    global _broadcaster_instance
    if _broadcaster_instance is None:
        _broadcaster_instance = WebSocketBroadcaster()
    return _broadcaster_instance
