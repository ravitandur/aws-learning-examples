"""
🚀 STOP LOSS HANDLER

Handles Stop Loss Check sub-events from Active User Event Handler.
Monitors active positions for stop loss triggers and executes exits when hit.

Responsibilities:
- Query active positions for the user
- Check current prices against stop loss levels
- Trigger immediate exit when stop loss is hit
- Log stop loss events for analytics
"""

import json
import os
import sys
import boto3
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from decimal import Decimal

sys.path.append('/opt/python')
sys.path.append('/var/task')

from shared_utils.logger import setup_logger, log_lambda_event

logger = setup_logger(__name__)

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'ap-south-1'))
sqs_client = boto3.client('sqs', region_name=os.environ.get('REGION', 'ap-south-1'))


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handle Stop Loss Check events.

    Monitors positions and triggers exits when stop loss is hit.
    """
    log_lambda_event(logger, event, context)

    try:
        detail = event.get('detail', {})
        user_id = detail.get('user_id')
        sub_event_id = detail.get('sub_event_id')
        market_phase = detail.get('market_phase')
        monitoring_scope = detail.get('monitoring_scope', 'ALL_ACTIVE_POSITIONS')

        if not user_id:
            logger.error("Missing user_id in Stop Loss Check event")
            return create_error_response("Missing user_id")

        logger.info(f"Processing Stop Loss Check for user {user_id}")
        logger.info(f"Market Phase: {market_phase}, Scope: {monitoring_scope}")

        # Get current IST time
        current_utc = datetime.now(timezone.utc)
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        current_ist = current_utc.astimezone(ist_offset)

        # Query active positions
        positions = query_active_positions(user_id)

        if not positions:
            logger.info(f"No active positions for user {user_id}")
            return create_success_response(user_id, sub_event_id, 0, 0, [])

        # Check each position for stop loss
        stop_loss_triggered = []
        for position in positions:
            result = check_stop_loss_for_position(position, current_ist)
            if result.get('triggered'):
                stop_loss_triggered.append(result)
                # Queue immediate exit
                queue_stop_loss_exit(user_id, position, result, current_ist)

        logger.info(f"Checked {len(positions)} positions, {len(stop_loss_triggered)} stop losses triggered")

        return create_success_response(
            user_id, sub_event_id,
            len(positions), len(stop_loss_triggered),
            stop_loss_triggered
        )

    except Exception as e:
        logger.error(f"Error in Stop Loss Handler: {str(e)}")
        return create_error_response(str(e))


def query_active_positions(user_id: str) -> List[Dict]:
    """Query active positions for the user from execution history."""
    try:
        table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])

        # Query today's executions with OPEN status
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            FilterExpression='#status = :open_status',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':prefix': f'{today}#',
                ':open_status': 'OPEN'
            },
            ExpressionAttributeNames={
                '#status': 'position_status'
            }
        )

        positions = response.get('Items', [])
        logger.info(f"Found {len(positions)} active positions for user {user_id}")
        return positions

    except Exception as e:
        logger.error(f"Error querying active positions: {str(e)}")
        return []


def check_stop_loss_for_position(position: Dict, current_ist: datetime) -> Dict:
    """
    Check if stop loss is triggered for a position.

    Stop loss types supported:
    - PERCENTAGE: Stop at X% loss
    - POINTS: Stop at X points loss
    - ABSOLUTE: Stop at specific price level
    """
    try:
        position_id = position.get('position_id', position.get('sort_key'))
        strategy_id = position.get('strategy_id')

        # Get stop loss configuration from position
        stop_loss_config = position.get('stop_loss', {})
        stop_loss_type = stop_loss_config.get('type', 'PERCENTAGE')
        stop_loss_value = float(stop_loss_config.get('value', 0))

        if stop_loss_value == 0:
            return {'position_id': position_id, 'triggered': False, 'reason': 'No stop loss configured'}

        # Get current P&L
        entry_price = float(position.get('entry_price', 0))
        current_price = float(position.get('current_price', entry_price))
        quantity = int(position.get('quantity', 0))
        position_type = position.get('position_type', 'LONG')  # LONG or SHORT

        # Calculate P&L based on position type
        if position_type == 'LONG':
            pnl_points = current_price - entry_price
        else:
            pnl_points = entry_price - current_price

        pnl_percentage = (pnl_points / entry_price * 100) if entry_price > 0 else 0
        pnl_absolute = pnl_points * quantity

        # Check stop loss based on type
        triggered = False
        trigger_reason = ''

        if stop_loss_type == 'PERCENTAGE':
            if pnl_percentage <= -stop_loss_value:
                triggered = True
                trigger_reason = f"Loss {pnl_percentage:.2f}% exceeded stop loss {stop_loss_value}%"

        elif stop_loss_type == 'POINTS':
            if pnl_points <= -stop_loss_value:
                triggered = True
                trigger_reason = f"Loss {pnl_points:.2f} points exceeded stop loss {stop_loss_value} points"

        elif stop_loss_type == 'ABSOLUTE':
            if pnl_absolute <= -stop_loss_value:
                triggered = True
                trigger_reason = f"Loss ₹{pnl_absolute:.2f} exceeded stop loss ₹{stop_loss_value}"

        return {
            'position_id': position_id,
            'strategy_id': strategy_id,
            'triggered': triggered,
            'reason': trigger_reason,
            'entry_price': entry_price,
            'current_price': current_price,
            'pnl_points': pnl_points,
            'pnl_percentage': pnl_percentage,
            'pnl_absolute': pnl_absolute,
            'stop_loss_type': stop_loss_type,
            'stop_loss_value': stop_loss_value,
            'check_time': current_ist.isoformat()
        }

    except Exception as e:
        logger.error(f"Error checking stop loss: {str(e)}")
        return {'position_id': position.get('position_id'), 'triggered': False, 'error': str(e)}


def queue_stop_loss_exit(user_id: str, position: Dict, trigger_result: Dict,
                          current_ist: datetime) -> None:
    """Queue immediate exit for stop loss triggered position."""
    try:
        queue_url = os.environ.get('SINGLE_STRATEGY_QUEUE_URL')
        if not queue_url:
            logger.error("SINGLE_STRATEGY_QUEUE_URL not configured")
            return

        message = {
            'user_id': user_id,
            'strategy_id': trigger_result.get('strategy_id'),
            'position_id': trigger_result.get('position_id'),
            'execution_type': 'STOP_LOSS_EXIT',
            'trigger_reason': trigger_result.get('reason'),
            'trigger_time': current_ist.isoformat(),
            'pnl_at_exit': trigger_result.get('pnl_absolute'),
            'source': 'stop_loss_handler',
            'priority': 'CRITICAL'
        }

        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, cls=DecimalEncoder),
            MessageGroupId=user_id,
            MessageDeduplicationId=f"SL_{trigger_result.get('position_id')}_{current_ist.strftime('%Y%m%d%H%M')}"
        )

        logger.info(f"Queued STOP_LOSS_EXIT for position {trigger_result.get('position_id')}")

    except Exception as e:
        logger.error(f"Error queuing stop loss exit: {str(e)}")


def create_success_response(user_id: str, sub_event_id: str,
                            positions_checked: int, stop_losses_triggered: int,
                            triggered_details: List) -> Dict:
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'user_id': user_id,
            'sub_event_id': sub_event_id,
            'positions_checked': positions_checked,
            'stop_losses_triggered': stop_losses_triggered,
            'triggered_details': triggered_details
        }, cls=DecimalEncoder)
    }


def create_error_response(error: str) -> Dict:
    return {
        'statusCode': 500,
        'body': json.dumps({
            'success': False,
            'error': error
        })
    }
