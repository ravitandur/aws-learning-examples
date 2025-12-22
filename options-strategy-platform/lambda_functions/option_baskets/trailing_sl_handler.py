"""
🚀 TRAILING STOP LOSS HANDLER

Handles Trailing Stop Loss Check sub-events from Active User Event Handler.
Monitors positions and adjusts trailing stop losses as price moves favorably.

Responsibilities:
- Query active positions with trailing SL configured
- Check if price has moved favorably to adjust SL
- Update stop loss levels in database
- Trigger exit if trailing SL is hit
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
    Handle Trailing Stop Loss Check events.

    Monitors positions and adjusts/triggers trailing stop losses.
    """
    log_lambda_event(logger, event, context)

    try:
        detail = event.get('detail', {})
        user_id = detail.get('user_id')
        sub_event_id = detail.get('sub_event_id')
        market_phase = detail.get('market_phase')
        adjustment_enabled = detail.get('adjustment_enabled', True)

        if not user_id:
            logger.error("Missing user_id in Trailing SL Check event")
            return create_error_response("Missing user_id")

        logger.info(f"Processing Trailing SL Check for user {user_id}")
        logger.info(f"Market Phase: {market_phase}, Adjustment Enabled: {adjustment_enabled}")

        # Get current IST time
        current_utc = datetime.now(timezone.utc)
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        current_ist = current_utc.astimezone(ist_offset)

        # Query active positions with trailing SL
        positions = query_positions_with_trailing_sl(user_id)

        if not positions:
            logger.info(f"No positions with trailing SL for user {user_id}")
            return create_success_response(user_id, sub_event_id, 0, 0, 0, [])

        # Check and adjust trailing SL for each position
        adjustments = []
        exits_triggered = []

        for position in positions:
            result = process_trailing_sl(position, current_ist, adjustment_enabled)

            if result.get('adjusted'):
                adjustments.append(result)
                # Update the stop loss in database
                update_trailing_sl_in_db(position, result)

            if result.get('exit_triggered'):
                exits_triggered.append(result)
                # Queue exit
                queue_trailing_sl_exit(user_id, position, result, current_ist)

        logger.info(f"Processed {len(positions)} positions: {len(adjustments)} adjusted, {len(exits_triggered)} exits")

        return create_success_response(
            user_id, sub_event_id,
            len(positions), len(adjustments), len(exits_triggered),
            adjustments + exits_triggered
        )

    except Exception as e:
        logger.error(f"Error in Trailing SL Handler: {str(e)}")
        return create_error_response(str(e))


def query_positions_with_trailing_sl(user_id: str) -> List[Dict]:
    """Query active positions with trailing stop loss configured."""
    try:
        table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            FilterExpression='#status = :open_status AND attribute_exists(trailing_sl)',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':prefix': f'{today}#',
                ':open_status': 'OPEN'
            },
            ExpressionAttributeNames={
                '#status': 'position_status'
            }
        )

        return response.get('Items', [])

    except Exception as e:
        logger.error(f"Error querying positions with trailing SL: {str(e)}")
        return []


def process_trailing_sl(position: Dict, current_ist: datetime,
                        adjustment_enabled: bool) -> Dict:
    """
    Process trailing stop loss for a position.

    Trailing SL types:
    - PERCENTAGE: Trail by X% from peak
    - POINTS: Trail by X points from peak
    """
    try:
        position_id = position.get('position_id', position.get('sort_key'))
        strategy_id = position.get('strategy_id')

        # Get trailing SL configuration
        trailing_config = position.get('trailing_sl', {})
        trail_type = trailing_config.get('type', 'PERCENTAGE')
        trail_value = float(trailing_config.get('value', 0))

        if trail_value == 0:
            return {'position_id': position_id, 'adjusted': False, 'exit_triggered': False}

        # Get prices
        entry_price = float(position.get('entry_price', 0))
        current_price = float(position.get('current_price', entry_price))
        peak_price = float(position.get('peak_price', entry_price))
        current_sl = float(position.get('current_stop_loss', 0))
        position_type = position.get('position_type', 'LONG')

        # Update peak price if current price is higher (for LONG) or lower (for SHORT)
        new_peak = peak_price
        if position_type == 'LONG' and current_price > peak_price:
            new_peak = current_price
        elif position_type == 'SHORT' and current_price < peak_price:
            new_peak = current_price

        # Calculate new trailing SL level
        if trail_type == 'PERCENTAGE':
            if position_type == 'LONG':
                new_sl = new_peak * (1 - trail_value / 100)
            else:
                new_sl = new_peak * (1 + trail_value / 100)
        else:  # POINTS
            if position_type == 'LONG':
                new_sl = new_peak - trail_value
            else:
                new_sl = new_peak + trail_value

        # Check if SL should be adjusted (only tighten, never loosen)
        adjusted = False
        if adjustment_enabled:
            if position_type == 'LONG' and new_sl > current_sl:
                adjusted = True
            elif position_type == 'SHORT' and new_sl < current_sl:
                adjusted = True

        # Check if exit is triggered
        exit_triggered = False
        exit_reason = ''
        if position_type == 'LONG' and current_price <= current_sl:
            exit_triggered = True
            exit_reason = f"Price {current_price} hit trailing SL {current_sl}"
        elif position_type == 'SHORT' and current_price >= current_sl:
            exit_triggered = True
            exit_reason = f"Price {current_price} hit trailing SL {current_sl}"

        return {
            'position_id': position_id,
            'strategy_id': strategy_id,
            'adjusted': adjusted,
            'exit_triggered': exit_triggered,
            'exit_reason': exit_reason,
            'old_sl': current_sl,
            'new_sl': new_sl if adjusted else current_sl,
            'peak_price': new_peak,
            'current_price': current_price,
            'trail_type': trail_type,
            'trail_value': trail_value,
            'check_time': current_ist.isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing trailing SL: {str(e)}")
        return {'position_id': position.get('position_id'), 'adjusted': False, 'exit_triggered': False, 'error': str(e)}


def update_trailing_sl_in_db(position: Dict, result: Dict) -> None:
    """Update the trailing stop loss level in database."""
    try:
        table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])

        table.update_item(
            Key={
                'user_id': position.get('user_id'),
                'sort_key': position.get('sort_key')
            },
            UpdateExpression='SET current_stop_loss = :new_sl, peak_price = :peak, sl_updated_at = :time',
            ExpressionAttributeValues={
                ':new_sl': Decimal(str(result.get('new_sl'))),
                ':peak': Decimal(str(result.get('peak_price'))),
                ':time': result.get('check_time')
            }
        )

        logger.info(f"Updated trailing SL for position {result.get('position_id')}: {result.get('new_sl')}")

    except Exception as e:
        logger.error(f"Error updating trailing SL in DB: {str(e)}")


def queue_trailing_sl_exit(user_id: str, position: Dict, result: Dict,
                            current_ist: datetime) -> None:
    """Queue exit for trailing SL triggered position."""
    try:
        queue_url = os.environ.get('SINGLE_STRATEGY_QUEUE_URL')
        if not queue_url:
            return

        message = {
            'user_id': user_id,
            'strategy_id': result.get('strategy_id'),
            'position_id': result.get('position_id'),
            'execution_type': 'TRAILING_SL_EXIT',
            'trigger_reason': result.get('exit_reason'),
            'trigger_time': current_ist.isoformat(),
            'exit_price': result.get('current_price'),
            'source': 'trailing_sl_handler',
            'priority': 'CRITICAL'
        }

        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, cls=DecimalEncoder),
            MessageGroupId=user_id,
            MessageDeduplicationId=f"TSL_{result.get('position_id')}_{current_ist.strftime('%Y%m%d%H%M')}"
        )

        logger.info(f"Queued TRAILING_SL_EXIT for position {result.get('position_id')}")

    except Exception as e:
        logger.error(f"Error queuing trailing SL exit: {str(e)}")


def create_success_response(user_id: str, sub_event_id: str,
                            positions_checked: int, adjustments: int,
                            exits_triggered: int, details: List) -> Dict:
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'user_id': user_id,
            'sub_event_id': sub_event_id,
            'positions_checked': positions_checked,
            'adjustments_made': adjustments,
            'exits_triggered': exits_triggered,
            'details': details
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
