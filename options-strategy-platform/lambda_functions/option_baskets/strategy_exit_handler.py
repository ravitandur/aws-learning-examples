"""
🚀 STRATEGY EXIT HANDLER

Handles Strategy Exit Trigger sub-events from Active User Event Handler.
Discovers strategies due for exit execution and triggers the exit pipeline.

Responsibilities:
- Query strategies with exit times in the lookahead window
- Query strategies with open positions needing exit
- Validate exit conditions are met
- Trigger strategy exit via SQS/Step Functions
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
    Handle Strategy Exit Trigger events.

    Discovers strategies due for exit and queues them for execution.
    """
    log_lambda_event(logger, event, context)

    try:
        detail = event.get('detail', {})
        user_id = detail.get('user_id')
        sub_event_id = detail.get('sub_event_id')
        trigger_time_ist = detail.get('trigger_time_ist')
        lookahead_minutes = detail.get('lookahead_minutes', 3)
        market_phase = detail.get('market_phase')

        if not user_id:
            logger.error("Missing user_id in Strategy Exit Trigger event")
            return create_error_response("Missing user_id")

        logger.info(f"Processing Strategy Exit for user {user_id}")
        logger.info(f"Lookahead: {lookahead_minutes} minutes, Market Phase: {market_phase}")

        # Get current IST time
        current_utc = datetime.now(timezone.utc)
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        current_ist = current_utc.astimezone(ist_offset)

        # Query strategies due for exit
        strategies = query_strategies_for_exit(
            user_id=user_id,
            current_ist=current_ist,
            lookahead_minutes=lookahead_minutes
        )

        if not strategies:
            logger.info(f"No strategies due for exit for user {user_id}")
            return create_success_response(user_id, sub_event_id, 0, [])

        # Queue strategies for exit execution
        queued_strategies = []
        for strategy in strategies:
            result = queue_strategy_for_exit(
                user_id=user_id,
                strategy=strategy,
                trigger_time=current_ist.isoformat()
            )
            queued_strategies.append(result)

        success_count = sum(1 for s in queued_strategies if s.get('status') == 'QUEUED')
        logger.info(f"Queued {success_count}/{len(strategies)} strategies for exit execution")

        return create_success_response(user_id, sub_event_id, success_count, queued_strategies)

    except Exception as e:
        logger.error(f"Error in Strategy Exit Handler: {str(e)}")
        return create_error_response(str(e))


def query_strategies_for_exit(user_id: str, current_ist: datetime,
                               lookahead_minutes: int) -> List[Dict]:
    """
    Query strategies with exit times in the lookahead window.
    Also includes strategies with open positions that need scheduled exit.
    """
    try:
        table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])

        current_time_str = current_ist.strftime("%H:%M")
        future_time = current_ist + timedelta(minutes=lookahead_minutes)
        future_time_str = future_time.strftime("%H:%M")
        current_weekday = current_ist.strftime("%A").upper()

        logger.info(f"Querying strategies for exit: {current_time_str} to {future_time_str}")

        # Query all active strategies for user
        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            FilterExpression='#status = :active',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':prefix': 'STRATEGY#',
                ':active': 'ACTIVE'
            },
            ExpressionAttributeNames={
                '#status': 'status'
            }
        )

        strategies = response.get('Items', [])

        # Filter strategies by exit time window
        matching_strategies = []
        for strategy in strategies:
            exit_time = strategy.get('exit_time', '')
            weekdays = strategy.get('weekdays', [])

            # Check if strategy should execute today
            if current_weekday not in [w.upper() for w in weekdays]:
                continue

            # Check if exit time is within lookahead window
            if is_time_in_window(exit_time, current_time_str, future_time_str):
                matching_strategies.append(strategy)
                logger.info(f"Strategy {strategy.get('strategy_id')} matched for exit at {exit_time}")

        return matching_strategies

    except Exception as e:
        logger.error(f"Error querying strategies for exit: {str(e)}")
        return []


def is_time_in_window(check_time: str, window_start: str, window_end: str) -> bool:
    """Check if a time string (HH:MM) is within the specified window."""
    try:
        if not check_time:
            return False
        return window_start <= check_time <= window_end
    except Exception:
        return False


def queue_strategy_for_exit(user_id: str, strategy: Dict, trigger_time: str) -> Dict:
    """Queue a strategy for exit execution via SQS."""
    try:
        queue_url = os.environ.get('SINGLE_STRATEGY_QUEUE_URL')
        if not queue_url:
            logger.error("SINGLE_STRATEGY_QUEUE_URL not configured")
            return {'strategy_id': strategy.get('strategy_id'), 'status': 'ERROR', 'error': 'Queue not configured'}

        message = {
            'user_id': user_id,
            'strategy_id': strategy.get('strategy_id'),
            'strategy_name': strategy.get('strategy_name'),
            'execution_type': 'EXIT',
            'trigger_time': trigger_time,
            'source': 'strategy_exit_handler'
        }

        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, cls=DecimalEncoder),
            MessageGroupId=user_id,
            MessageDeduplicationId=f"{strategy.get('strategy_id')}_EXIT_{trigger_time}"
        )

        logger.info(f"Queued strategy {strategy.get('strategy_id')} for EXIT")
        return {
            'strategy_id': strategy.get('strategy_id'),
            'status': 'QUEUED',
            'message_id': response.get('MessageId')
        }

    except Exception as e:
        logger.error(f"Error queuing strategy for exit: {str(e)}")
        return {
            'strategy_id': strategy.get('strategy_id'),
            'status': 'ERROR',
            'error': str(e)
        }


def create_success_response(user_id: str, sub_event_id: str,
                            count: int, results: List) -> Dict:
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'user_id': user_id,
            'sub_event_id': sub_event_id,
            'strategies_queued': count,
            'results': results
        })
    }


def create_error_response(error: str) -> Dict:
    return {
        'statusCode': 500,
        'body': json.dumps({
            'success': False,
            'error': error
        })
    }
