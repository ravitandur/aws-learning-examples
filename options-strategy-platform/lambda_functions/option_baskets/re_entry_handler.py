"""
🚀 RE-ENTRY HANDLER

Handles Re-Entry Check sub-events from Active User Event Handler.
Monitors strategies for re-entry conditions after stop loss or position close.

Responsibilities:
- Query strategies with re-entry configured
- Check if re-entry conditions are met
- Validate re-entry count limits
- Trigger new entry if conditions satisfied
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
    Handle Re-Entry Check events.

    Monitors strategies for re-entry conditions and triggers new entries.
    """
    log_lambda_event(logger, event, context)

    try:
        detail = event.get('detail', {})
        user_id = detail.get('user_id')
        sub_event_id = detail.get('sub_event_id')
        market_phase = detail.get('market_phase')
        conditions = detail.get('conditions', ['STOP_LOSS_HIT', 'POSITION_CLOSED'])

        if not user_id:
            logger.error("Missing user_id in Re-Entry Check event")
            return create_error_response("Missing user_id")

        logger.info(f"Processing Re-Entry Check for user {user_id}")
        logger.info(f"Market Phase: {market_phase}, Conditions: {conditions}")

        # Get current IST time
        current_utc = datetime.now(timezone.utc)
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        current_ist = current_utc.astimezone(ist_offset)

        # Query strategies with re-entry configured
        strategies = query_strategies_for_re_entry(user_id)

        if not strategies:
            logger.info(f"No strategies eligible for re-entry for user {user_id}")
            return create_success_response(user_id, sub_event_id, 0, 0, [])

        # Check re-entry conditions for each strategy
        re_entries = []
        for strategy in strategies:
            result = check_re_entry_conditions(strategy, conditions, current_ist)
            if result.get('eligible'):
                re_entries.append(result)
                # Queue re-entry
                queue_re_entry(user_id, strategy, result, current_ist)

        logger.info(f"Checked {len(strategies)} strategies, {len(re_entries)} eligible for re-entry")

        return create_success_response(
            user_id, sub_event_id,
            len(strategies), len(re_entries),
            re_entries
        )

    except Exception as e:
        logger.error(f"Error in Re-Entry Handler: {str(e)}")
        return create_error_response(str(e))


def query_strategies_for_re_entry(user_id: str) -> List[Dict]:
    """Query strategies with re-entry feature enabled."""
    try:
        table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])

        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            FilterExpression='#status = :active AND attribute_exists(re_entry)',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':prefix': 'STRATEGY#',
                ':active': 'ACTIVE'
            },
            ExpressionAttributeNames={
                '#status': 'status'
            }
        )

        return response.get('Items', [])

    except Exception as e:
        logger.error(f"Error querying strategies for re-entry: {str(e)}")
        return []


def check_re_entry_conditions(strategy: Dict, conditions: List[str],
                               current_ist: datetime) -> Dict:
    """
    Check if re-entry conditions are met for a strategy.

    Conditions:
    - STOP_LOSS_HIT: Strategy exited due to stop loss
    - POSITION_CLOSED: Position was closed (manually or by target)
    - COOLDOWN_PASSED: Minimum time since last exit has passed
    - MAX_RE_ENTRIES: Haven't exceeded max re-entry count
    """
    try:
        strategy_id = strategy.get('strategy_id')
        re_entry_config = strategy.get('re_entry', {})

        # Check if re-entry is enabled
        if not re_entry_config.get('enabled', False):
            return {'strategy_id': strategy_id, 'eligible': False, 'reason': 'Re-entry disabled'}

        max_re_entries = re_entry_config.get('max_count', 1)
        current_re_entries = strategy.get('re_entry_count', 0)
        cooldown_minutes = re_entry_config.get('cooldown_minutes', 5)
        last_exit_time = strategy.get('last_exit_time')
        exit_reason = strategy.get('last_exit_reason', '')

        # Check max re-entries
        if current_re_entries >= max_re_entries:
            return {
                'strategy_id': strategy_id,
                'eligible': False,
                'reason': f'Max re-entries ({max_re_entries}) reached'
            }

        # Check exit reason matches conditions
        exit_reason_match = False
        if 'STOP_LOSS_HIT' in conditions and 'STOP_LOSS' in exit_reason.upper():
            exit_reason_match = True
        if 'POSITION_CLOSED' in conditions and exit_reason:
            exit_reason_match = True

        if not exit_reason_match:
            return {
                'strategy_id': strategy_id,
                'eligible': False,
                'reason': f'Exit reason ({exit_reason}) does not match conditions'
            }

        # Check cooldown
        if last_exit_time:
            try:
                last_exit_dt = datetime.fromisoformat(last_exit_time.replace('Z', '+00:00'))
                ist_offset = timezone(timedelta(hours=5, minutes=30))
                last_exit_ist = last_exit_dt.astimezone(ist_offset)
                time_since_exit = (current_ist - last_exit_ist).total_seconds() / 60

                if time_since_exit < cooldown_minutes:
                    return {
                        'strategy_id': strategy_id,
                        'eligible': False,
                        'reason': f'Cooldown not passed ({time_since_exit:.1f}/{cooldown_minutes} min)'
                    }
            except Exception:
                pass

        # All conditions met
        return {
            'strategy_id': strategy_id,
            'strategy_name': strategy.get('strategy_name'),
            'eligible': True,
            'reason': 'All re-entry conditions met',
            're_entry_number': current_re_entries + 1,
            'max_re_entries': max_re_entries,
            'exit_reason': exit_reason,
            'check_time': current_ist.isoformat()
        }

    except Exception as e:
        logger.error(f"Error checking re-entry conditions: {str(e)}")
        return {'strategy_id': strategy.get('strategy_id'), 'eligible': False, 'error': str(e)}


def queue_re_entry(user_id: str, strategy: Dict, result: Dict,
                    current_ist: datetime) -> None:
    """Queue a strategy re-entry execution."""
    try:
        queue_url = os.environ.get('SINGLE_STRATEGY_QUEUE_URL')
        if not queue_url:
            return

        message = {
            'user_id': user_id,
            'strategy_id': result.get('strategy_id'),
            'strategy_name': result.get('strategy_name'),
            'execution_type': 'RE_ENTRY',
            're_entry_number': result.get('re_entry_number'),
            'trigger_time': current_ist.isoformat(),
            'source': 're_entry_handler',
            'priority': 'NORMAL'
        }

        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, cls=DecimalEncoder),
            MessageGroupId=user_id,
            MessageDeduplicationId=f"RE_{result.get('strategy_id')}_{result.get('re_entry_number')}_{current_ist.strftime('%Y%m%d')}"
        )

        logger.info(f"Queued RE_ENTRY #{result.get('re_entry_number')} for strategy {result.get('strategy_id')}")

    except Exception as e:
        logger.error(f"Error queuing re-entry: {str(e)}")


def create_success_response(user_id: str, sub_event_id: str,
                            strategies_checked: int, re_entries_queued: int,
                            re_entry_details: List) -> Dict:
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'user_id': user_id,
            'sub_event_id': sub_event_id,
            'strategies_checked': strategies_checked,
            're_entries_queued': re_entries_queued,
            're_entry_details': re_entry_details
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
