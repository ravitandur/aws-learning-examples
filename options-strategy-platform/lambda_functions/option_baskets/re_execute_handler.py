"""
🚀 RE-EXECUTE HANDLER

Handles Re-Execute Check sub-events from Active User Event Handler.
Retries failed strategy executions with configurable retry logic.

Responsibilities:
- Query failed executions for the user
- Check retry eligibility (max retries, cooldown)
- Retry execution with exponential backoff
- Log retry attempts and outcomes
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
    Handle Re-Execute Check events.

    Retries failed executions that are eligible for retry.
    """
    log_lambda_event(logger, event, context)

    try:
        detail = event.get('detail', {})
        user_id = detail.get('user_id')
        sub_event_id = detail.get('sub_event_id')
        market_phase = detail.get('market_phase')
        max_retries = detail.get('max_retries', 3)
        conditions = detail.get('conditions', ['EXECUTION_FAILED', 'ORDER_REJECTED'])

        if not user_id:
            logger.error("Missing user_id in Re-Execute Check event")
            return create_error_response("Missing user_id")

        logger.info(f"Processing Re-Execute Check for user {user_id}")
        logger.info(f"Market Phase: {market_phase}, Max Retries: {max_retries}")

        # Get current IST time
        current_utc = datetime.now(timezone.utc)
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        current_ist = current_utc.astimezone(ist_offset)

        # Query failed executions
        failed_executions = query_failed_executions(user_id, conditions)

        if not failed_executions:
            logger.info(f"No failed executions for user {user_id}")
            return create_success_response(user_id, sub_event_id, 0, 0, [])

        # Check and retry each failed execution
        retries = []
        for execution in failed_executions:
            result = check_retry_eligibility(execution, max_retries, current_ist)
            if result.get('eligible'):
                retries.append(result)
                # Queue retry
                queue_retry_execution(user_id, execution, result, current_ist)

        logger.info(f"Checked {len(failed_executions)} failures, {len(retries)} eligible for retry")

        return create_success_response(
            user_id, sub_event_id,
            len(failed_executions), len(retries),
            retries
        )

    except Exception as e:
        logger.error(f"Error in Re-Execute Handler: {str(e)}")
        return create_error_response(str(e))


def query_failed_executions(user_id: str, conditions: List[str]) -> List[Dict]:
    """Query failed executions for the user from today."""
    try:
        table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Build filter for failure conditions
        filter_conditions = []
        expression_values = {
            ':user_id': user_id,
            ':prefix': f'{today}#'
        }

        if 'EXECUTION_FAILED' in conditions:
            filter_conditions.append('execution_status = :failed')
            expression_values[':failed'] = 'FAILED'

        if 'ORDER_REJECTED' in conditions:
            filter_conditions.append('execution_status = :rejected')
            expression_values[':rejected'] = 'REJECTED'

        filter_expr = ' OR '.join(filter_conditions) if filter_conditions else 'execution_status = :failed'

        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            FilterExpression=filter_expr,
            ExpressionAttributeValues=expression_values
        )

        return response.get('Items', [])

    except Exception as e:
        logger.error(f"Error querying failed executions: {str(e)}")
        return []


def check_retry_eligibility(execution: Dict, max_retries: int,
                             current_ist: datetime) -> Dict:
    """
    Check if a failed execution is eligible for retry.

    Criteria:
    - Haven't exceeded max retry count
    - Cooldown period has passed (exponential backoff)
    - Failure reason is retryable
    """
    try:
        execution_id = execution.get('sort_key')
        strategy_id = execution.get('strategy_id')
        failure_reason = execution.get('failure_reason', '')
        retry_count = int(execution.get('retry_count', 0))
        last_retry_time = execution.get('last_retry_time')

        # Check max retries
        if retry_count >= max_retries:
            return {
                'execution_id': execution_id,
                'eligible': False,
                'reason': f'Max retries ({max_retries}) exceeded'
            }

        # Check if failure reason is retryable
        non_retryable = ['INSUFFICIENT_FUNDS', 'INVALID_SYMBOL', 'MARKET_CLOSED', 'INVALID_QUANTITY']
        if any(reason in failure_reason.upper() for reason in non_retryable):
            return {
                'execution_id': execution_id,
                'eligible': False,
                'reason': f'Non-retryable failure: {failure_reason}'
            }

        # Check cooldown with exponential backoff
        cooldown_minutes = 2 ** retry_count  # 1, 2, 4, 8 minutes
        if last_retry_time:
            try:
                last_retry_dt = datetime.fromisoformat(last_retry_time.replace('Z', '+00:00'))
                ist_offset = timezone(timedelta(hours=5, minutes=30))
                last_retry_ist = last_retry_dt.astimezone(ist_offset)
                time_since_retry = (current_ist - last_retry_ist).total_seconds() / 60

                if time_since_retry < cooldown_minutes:
                    return {
                        'execution_id': execution_id,
                        'eligible': False,
                        'reason': f'Cooldown not passed ({time_since_retry:.1f}/{cooldown_minutes} min)'
                    }
            except Exception:
                pass

        # Eligible for retry
        return {
            'execution_id': execution_id,
            'strategy_id': strategy_id,
            'strategy_name': execution.get('strategy_name'),
            'eligible': True,
            'reason': 'Eligible for retry',
            'retry_number': retry_count + 1,
            'max_retries': max_retries,
            'failure_reason': failure_reason,
            'check_time': current_ist.isoformat()
        }

    except Exception as e:
        logger.error(f"Error checking retry eligibility: {str(e)}")
        return {'execution_id': execution.get('sort_key'), 'eligible': False, 'error': str(e)}


def queue_retry_execution(user_id: str, execution: Dict, result: Dict,
                           current_ist: datetime) -> None:
    """Queue a retry execution."""
    try:
        queue_url = os.environ.get('SINGLE_STRATEGY_QUEUE_URL')
        if not queue_url:
            return

        # Update retry count in database
        update_retry_count(execution, result.get('retry_number'), current_ist)

        message = {
            'user_id': user_id,
            'strategy_id': result.get('strategy_id'),
            'strategy_name': result.get('strategy_name'),
            'execution_type': 'RETRY',
            'original_execution_id': result.get('execution_id'),
            'retry_number': result.get('retry_number'),
            'trigger_time': current_ist.isoformat(),
            'source': 're_execute_handler',
            'priority': 'HIGH'
        }

        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, cls=DecimalEncoder),
            MessageGroupId=user_id,
            MessageDeduplicationId=f"RETRY_{result.get('execution_id')}_{result.get('retry_number')}"
        )

        logger.info(f"Queued RETRY #{result.get('retry_number')} for execution {result.get('execution_id')}")

    except Exception as e:
        logger.error(f"Error queuing retry execution: {str(e)}")


def update_retry_count(execution: Dict, retry_number: int, current_ist: datetime) -> None:
    """Update the retry count in the execution record."""
    try:
        table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])

        table.update_item(
            Key={
                'user_id': execution.get('user_id'),
                'sort_key': execution.get('sort_key')
            },
            UpdateExpression='SET retry_count = :count, last_retry_time = :time',
            ExpressionAttributeValues={
                ':count': retry_number,
                ':time': current_ist.isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Error updating retry count: {str(e)}")


def create_success_response(user_id: str, sub_event_id: str,
                            failures_checked: int, retries_queued: int,
                            retry_details: List) -> Dict:
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'user_id': user_id,
            'sub_event_id': sub_event_id,
            'failures_checked': failures_checked,
            'retries_queued': retries_queued,
            'retry_details': retry_details
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
