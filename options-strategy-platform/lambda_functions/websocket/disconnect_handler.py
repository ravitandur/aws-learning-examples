"""
WebSocket $disconnect Route Handler
Cleans up connection info from DynamoDB when client disconnects
"""

import json
import os
import logging
from typing import Any, Dict

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(os.environ.get('WEBSOCKET_CONNECTIONS_TABLE', ''))


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket $disconnect route.
    Removes connection from DynamoDB.
    """
    logger.info(f"Disconnect event: {json.dumps(event)}")

    connection_id = event['requestContext']['connectionId']

    try:
        # Delete connection from DynamoDB
        connections_table.delete_item(
            Key={
                'connection_id': connection_id
            }
        )

        logger.info(f"Connection {connection_id} removed")

        return {
            'statusCode': 200,
            'body': 'Disconnected'
        }

    except Exception as e:
        logger.error(f"Error removing connection: {e}")
        # Still return 200 - client is disconnected regardless
        return {
            'statusCode': 200,
            'body': 'Disconnected'
        }
