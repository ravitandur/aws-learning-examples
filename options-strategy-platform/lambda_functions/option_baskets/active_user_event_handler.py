"""
🚀 ACTIVE USER EVENT HANDLER - Sub-Event Processor and Emitter

This Lambda handles Active User Events from EventBridge and processes all sub-events
for a single user. For each active broker configured for the user, it emits all
sub-events to ensure broker-specific processing.

Architecture:
1. Receive Active User Event
2. Query active brokers for the user
3. For each broker, emit all sub-events with broker context
4. Each sub-event handler processes broker-specific operations

Sub-Events Handled:
- strategy_entry: Discover and execute strategy entries
- strategy_exit: Discover and execute strategy exits
- stop_loss_check: Monitor positions for stop loss triggers
- target_profit_check: Monitor positions for target profit triggers
- trailing_sl_check: Adjust trailing stop losses
- duplicate_order_check: Validate for duplicate orders
- re_entry_check: Check re-entry conditions
- re_execute_check: Retry failed executions
- position_sync: Sync positions across brokers
"""

import json
import os
import sys
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

sys.path.append('/opt/python')
sys.path.append('/var/task')

from shared_utils.logger import setup_logger, log_lambda_event

logger = setup_logger(__name__)

eventbridge_client = boto3.client('events', region_name=os.environ.get('REGION', 'ap-south-1'))
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'ap-south-1'))


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    🚀 Active User Event Handler

    Receives Active User Events from EventBridge, queries active brokers for the user,
    and emits all sub-events for each broker to specialized handlers.
    """
    log_lambda_event(logger, event, context)

    try:
        detail = event.get('detail', {})
        user_id = detail.get('user_id')
        event_id = detail.get('event_id')
        trigger_time_ist = detail.get('trigger_time_ist')
        market_phase = detail.get('market_phase')
        sub_events = detail.get('sub_events', [])

        if not user_id:
            logger.error("❌ No user_id in Active User Event")
            return create_error_response("Missing user_id in event")

        logger.info(f"🚀 Processing Active User Event for user {user_id}")
        logger.info(f"📊 Event ID: {event_id}, Market Phase: {market_phase}")
        logger.info(f"📋 Sub-events to process: {len(sub_events)}")

        # Get active brokers for the user
        active_brokers = get_active_brokers_for_user(user_id)

        if not active_brokers:
            logger.warning(f"⚠️ No active brokers found for user {user_id}")
            return create_success_response(
                user_id, event_id, 0, 0, 0,
                [], "No active brokers configured"
            )

        logger.info(f"🏦 Found {len(active_brokers)} active brokers for user {user_id}")
        for broker in active_brokers:
            logger.info(f"  - {broker.get('broker_name', broker.get('broker_id'))} (client_id: {broker.get('client_id')})")

        # Process sub-events for each broker
        all_results = []
        total_events_emitted = 0

        for broker in active_brokers:
            broker_id = broker.get('broker_id')
            client_id = broker.get('client_id')
            broker_name = broker.get('broker_name', broker_id)

            logger.info(f"📤 Emitting sub-events for broker: {broker_name} (broker_id: {broker_id}, client_id: {client_id})")

            for sub_event in sub_events:
                result = process_sub_event_for_broker(
                    user_id=user_id,
                    broker=broker,
                    sub_event=sub_event,
                    market_phase=market_phase,
                    trigger_time_ist=trigger_time_ist,
                    parent_event_id=event_id
                )
                all_results.append(result)

                if result.get('status') == 'SUCCESS':
                    total_events_emitted += 1

        success_count = sum(1 for r in all_results if r.get('status') == 'SUCCESS')
        failed_count = sum(1 for r in all_results if r.get('status') == 'FAILED')

        logger.info(f"✅ Processed {len(all_results)} total sub-events across {len(active_brokers)} brokers")
        logger.info(f"📊 Success: {success_count}, Failed: {failed_count}")

        return create_success_response(
            user_id, event_id,
            len(active_brokers), len(sub_events), total_events_emitted,
            all_results, None
        )

    except Exception as e:
        logger.error(f"❌ Error processing Active User Event: {str(e)}")
        return create_error_response(str(e))


def get_active_brokers_for_user(user_id: str) -> List[Dict]:
    """
    Query active broker accounts for the user from the broker accounts table.
    Returns list of active broker configurations.
    """
    try:
        broker_table_name = os.environ.get('BROKER_ACCOUNTS_TABLE')
        if not broker_table_name:
            logger.warning("BROKER_ACCOUNTS_TABLE not configured, using fallback")
            return []

        table = dynamodb.Table(broker_table_name)

        response = table.query(
            KeyConditionExpression='user_id = :user_id',
            FilterExpression='#status = :active',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':active': 'active'
            },
            ExpressionAttributeNames={
                '#status': 'status'
            }
        )

        brokers = response.get('Items', [])
        logger.info(f"Found {len(brokers)} active brokers for user {user_id}")
        return brokers

    except Exception as e:
        logger.error(f"Error querying broker accounts: {str(e)}")
        return []


def process_sub_event_for_broker(user_id: str, broker: Dict, sub_event: Dict,
                                  market_phase: str, trigger_time_ist: str,
                                  parent_event_id: str) -> Dict[str, Any]:
    """
    Process a single sub-event for a specific broker.
    Emits the sub-event to EventBridge with broker context.
    """
    event_type = sub_event.get('event_type')
    enabled = sub_event.get('enabled', True)
    broker_id = broker.get('broker_id')
    client_id = broker.get('client_id')
    broker_name = broker.get('broker_name', broker_id)

    if not enabled:
        return {
            'event_type': event_type,
            'broker_id': broker_id,
            'client_id': client_id,
            'status': 'SKIPPED',
            'reason': 'disabled'
        }

    try:
        sub_event_detail = create_sub_event_detail_with_broker(
            user_id=user_id,
            broker=broker,
            event_type=event_type,
            sub_event_config=sub_event,
            market_phase=market_phase,
            trigger_time_ist=trigger_time_ist,
            parent_event_id=parent_event_id
        )

        result = emit_sub_event_to_eventbridge(sub_event_detail)

        logger.debug(f"📤 Emitted {event_type} for broker {broker_name} (client: {client_id})")
        return {
            'event_type': event_type,
            'broker_id': broker_id,
            'client_id': client_id,
            'broker_name': broker_name,
            'status': 'SUCCESS',
            'event_id': sub_event_detail['detail']['sub_event_id'],
            'eventbridge_result': result
        }

    except Exception as e:
        logger.error(f"❌ Error processing {event_type} for broker {broker_id} (client: {client_id}): {str(e)}")
        return {
            'event_type': event_type,
            'broker_id': broker_id,
            'client_id': client_id,
            'status': 'FAILED',
            'error': str(e)
        }


def create_sub_event_detail_with_broker(user_id: str, broker: Dict, event_type: str,
                                         sub_event_config: Dict, market_phase: str,
                                         trigger_time_ist: str,
                                         parent_event_id: str) -> Dict[str, Any]:
    """
    Create the detailed event payload for a specific sub-event type with broker context.

    The sub_event_config comes directly from event_emitter.py and contains all
    event-specific fields (lookahead_minutes, check_frequency, conditions, etc.)
    We simply add broker context and pass through all config fields.
    """
    sub_event_id = str(uuid.uuid4())
    broker_id = broker.get('broker_id')
    broker_name = broker.get('broker_name', broker_id)
    broker_type = broker.get('broker_type', 'UNKNOWN')
    client_id = broker.get('client_id')

    # Industry-standard EventBridge naming convention
    # Single source for all options trading events, routing via detail_type
    source = "qlalgo.options.trading"

    # Detail type mapping: {Category}.{Entity}.{Action}
    detail_type_mapping = {
        'strategy_entry': 'Strategy.Entry.Triggered',
        'strategy_exit': 'Strategy.Exit.Triggered',
        'stop_loss_check': 'Risk.StopLoss.Check',
        'target_profit_check': 'Risk.TargetProfit.Check',
        'trailing_sl_check': 'Risk.TrailingSL.Check',
        'duplicate_order_check': 'Validation.DuplicateOrder.Check',
        're_entry_check': 'Strategy.ReEntry.Check',
        're_execute_check': 'Strategy.ReExecute.Check',
        'position_sync': 'Sync.Position.Triggered'
    }

    detail_type = detail_type_mapping.get(event_type, f'Unknown.{event_type}')

    # Build event detail - merge broker context with all sub_event_config fields
    event_detail = {
        # Core identifiers
        'sub_event_id': sub_event_id,
        'parent_event_id': parent_event_id,
        'user_id': user_id,
        'event_type': event_type,
        'trigger_time_ist': trigger_time_ist,
        'market_phase': market_phase,
        'created_at': datetime.now(timezone.utc).isoformat(),

        # Broker context (critical for broker-specific processing)
        'broker_id': broker_id,
        'client_id': client_id,
        'broker_name': broker_name,
        'broker_type': broker_type,
        'broker_config': {
            'api_key_secret_arn': broker.get('api_key_secret_arn'),
            'is_authenticated': broker.get('is_authenticated', False),
            'oauth_status': broker.get('oauth_status', 'not_configured')
        }
    }

    # Pass through ALL fields from sub_event_config (from event_emitter.py)
    # This includes: priority, lookahead_minutes, check_frequency, conditions,
    # monitoring_scope, max_retries, dedup_strategy, adjustment_enabled, etc.
    for key, value in sub_event_config.items():
        if key != 'event_type' and key != 'enabled':  # Skip already handled fields
            event_detail[key] = value

    return {
        'source': source,
        'detail_type': detail_type,
        'detail': event_detail
    }


def emit_sub_event_to_eventbridge(event_detail: Dict[str, Any]) -> Dict[str, Any]:
    """
    Emit a sub-event to EventBridge for processing by specialized handlers.
    """
    try:
        event_entry = {
            'Source': event_detail['source'],
            'DetailType': event_detail['detail_type'],
            'Detail': json.dumps(event_detail['detail']),
            'Time': datetime.now(timezone.utc)
        }

        response = eventbridge_client.put_events(Entries=[event_entry])

        if response.get('FailedEntryCount', 0) > 0:
            error_msg = response['Entries'][0].get('ErrorMessage', 'Unknown error')
            logger.error(f"❌ Failed to emit sub-event: {error_msg}")
            return {'status': 'FAILED', 'error': error_msg}

        return {
            'status': 'SUCCESS',
            'event_id': response['Entries'][0].get('EventId')
        }

    except Exception as e:
        logger.error(f"❌ Error emitting sub-event to EventBridge: {str(e)}")
        return {'status': 'ERROR', 'error': str(e)}


def create_success_response(user_id: str, event_id: str,
                            brokers_count: int, sub_events_count: int,
                            events_emitted: int, results: List,
                            message: str = None) -> Dict[str, Any]:
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'user_id': user_id,
            'event_id': event_id,
            'brokers_processed': brokers_count,
            'sub_events_per_broker': sub_events_count,
            'total_events_emitted': events_emitted,
            'results': results,
            'message': message
        })
    }


def create_error_response(error_message: str) -> Dict[str, Any]:
    return {
        'statusCode': 500,
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }
