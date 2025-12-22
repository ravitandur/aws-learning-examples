"""
🚀 STRATEGY ENTRY HANDLER

Handles Strategy Entry Trigger sub-events from Active User Event Handler.
Discovers strategies due for entry execution and triggers the execution pipeline.

Key Features:
- Broker-specific strategy discovery (filters by client_id allocation)
- Uses UserScheduleDiscovery GSI for efficient day/time querying
- Uses AllocationsByBasket GSI for broker allocation validation
- Respects basket-level broker inheritance
- Emits Strategy Execution Events to EventBridge with pre-fetched allocation data

Hybrid Approach (Option 2):
- Passes allocation data already fetched (no re-query in executor)
- Executor only fetches strategy details (legs, underlying, etc.)
- Optimizes query count: 2 queries here + 1 query in executor = 3 total
"""

import json
import os
import sys
import boto3
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

sys.path.append('/opt/python')
sys.path.append('/var/task')

from shared_utils.logger import setup_logger, log_lambda_event

logger = setup_logger(__name__)

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'ap-south-1'))
eventbridge_client = boto3.client('events', region_name=os.environ.get('REGION', 'ap-south-1'))

# Cache for basket allocations to avoid duplicate queries within same invocation
_allocation_cache: Dict[str, List[Dict]] = {}


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handle Strategy Entry Trigger events from Active User Event Handler.

    Receives broker context and discovers strategies due for entry that are
    allocated to the specific broker/client_id. Emits execution events with
    pre-fetched allocation data.
    """
    log_lambda_event(logger, event, context)

    # Clear allocation cache at start of each invocation
    global _allocation_cache
    _allocation_cache = {}

    try:
        detail = event.get('detail', {})
        user_id = detail.get('user_id')
        sub_event_id = detail.get('sub_event_id')
        lookahead_minutes = detail.get('lookahead_minutes', 3)
        market_phase = detail.get('market_phase')

        # Broker context from active_user_event_handler
        broker_id = detail.get('broker_id')
        client_id = detail.get('client_id')
        broker_name = detail.get('broker_name')
        broker_config = detail.get('broker_config', {})

        # Validation
        if not user_id:
            logger.error("Missing user_id in Strategy Entry Trigger event")
            return create_error_response("Missing user_id")

        if not client_id:
            logger.error("Missing client_id in Strategy Entry Trigger event")
            return create_error_response("Missing client_id - broker context required")

        # Check broker authentication status
        if not broker_config.get('is_authenticated', False):
            logger.warning(f"Broker {broker_name} (client_id: {client_id}) not authenticated, skipping entry processing")
            return create_success_response(
                user_id, sub_event_id, 0, [],
                broker_id=broker_id,
                client_id=client_id,
                message="Broker not authenticated"
            )

        logger.info(f"🚀 Processing Strategy Entry for user {user_id}")
        logger.info(f"🏦 Broker: {broker_name} (client_id: {client_id})")
        logger.info(f"⏱️ Lookahead: {lookahead_minutes} minutes, Market Phase: {market_phase}")

        # Get current IST time
        current_utc = datetime.now(timezone.utc)
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        current_ist = current_utc.astimezone(ist_offset)
        current_weekday = get_weekday_abbr(current_ist)

        # Query strategies due for entry filtered by broker allocation
        strategies = query_strategies_for_entry(
            user_id=user_id,
            client_id=client_id,
            current_ist=current_ist,
            lookahead_minutes=lookahead_minutes
        )

        if not strategies:
            logger.info(f"No strategies due for entry for user {user_id} with broker {broker_name}")
            return create_success_response(
                user_id, sub_event_id, 0, [],
                broker_id=broker_id,
                client_id=client_id
            )

        logger.info(f"📋 Found {len(strategies)} strategies due for entry with {broker_name} allocation")

        # Emit execution events for each strategy with pre-fetched allocation
        emitted_strategies = []
        for strategy in strategies:
            # Get the specific allocation for this broker (already cached from query phase)
            allocation = get_allocation_for_broker(strategy.get('basket_id'), client_id)

            result = emit_strategy_execution_event(
                user_id=user_id,
                strategy=strategy,
                execution_type='ENTRY',
                weekday=current_weekday,
                broker_context={
                    'broker_id': broker_id,
                    'client_id': client_id,
                    'broker_name': broker_name,
                    'broker_config': broker_config
                },
                allocation=allocation
            )
            emitted_strategies.append(result)

        success_count = sum(1 for s in emitted_strategies if s.get('status') == 'EMITTED')
        logger.info(f"✅ Emitted {success_count}/{len(strategies)} strategy execution events")

        return create_success_response(
            user_id, sub_event_id, success_count, emitted_strategies,
            broker_id=broker_id,
            client_id=client_id
        )

    except Exception as e:
        logger.error(f"❌ Error in Strategy Entry Handler: {str(e)}")
        return create_error_response(str(e))


def get_weekday_abbr(dt: datetime) -> str:
    """Get weekday abbreviation (MON, TUE, WED, etc.) from datetime."""
    weekday_map = {
        'MONDAY': 'MON', 'TUESDAY': 'TUE', 'WEDNESDAY': 'WED',
        'THURSDAY': 'THU', 'FRIDAY': 'FRI', 'SATURDAY': 'SAT', 'SUNDAY': 'SUN'
    }
    weekday_full = dt.strftime("%A").upper()
    return weekday_map.get(weekday_full, weekday_full[:3])


def query_strategies_for_entry(
    user_id: str,
    client_id: str,
    current_ist: datetime,
    lookahead_minutes: int
) -> List[Dict]:
    """
    Query strategies with entry times in the lookahead window, filtered by broker allocation.

    Two-phase query approach:
    1. Query UserScheduleDiscovery GSI for strategies due at current weekday/time
    2. Filter by broker allocation - only return strategies whose basket has allocation for client_id

    Args:
        user_id: User identifier
        client_id: Broker client ID to filter by
        current_ist: Current IST datetime
        lookahead_minutes: Minutes to look ahead for strategy entries

    Returns:
        List of strategies due for entry that have allocation for the specified client_id
    """
    try:
        table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])

        # Calculate time window
        current_time_str = current_ist.strftime("%H:%M")
        future_time = current_ist + timedelta(minutes=lookahead_minutes)
        future_time_str = future_time.strftime("%H:%M")
        current_weekday = get_weekday_abbr(current_ist)

        logger.info(f"🔍 Querying strategies for entry: {current_weekday} {current_time_str} to {future_time_str}")

        # Phase 1: Query UserScheduleDiscovery GSI for ENTRY schedules on this weekday
        # Schedule key format: SCHEDULE#{WEEKDAY}#{TIME}#{TYPE}#{STRATEGY_ID}
        schedule_prefix = f"SCHEDULE#{current_weekday}#"

        response = table.query(
            IndexName='UserScheduleDiscovery',
            KeyConditionExpression='user_id = :user_id AND begins_with(schedule_key, :pattern)',
            FilterExpression='#status = :active AND execution_type = :entry',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':pattern': schedule_prefix,
                ':active': 'ACTIVE',
                ':entry': 'ENTRY'
            },
            ExpressionAttributeNames={'#status': 'status'},
            ProjectionExpression='strategy_id, basket_id, execution_time, execution_type, weekday, sort_key, schedule_key'
        )

        schedules = response.get('Items', [])
        logger.info(f"📊 Found {len(schedules)} ENTRY schedules for {current_weekday}")

        # Filter by time window
        time_matched_schedules = []
        for schedule in schedules:
            execution_time = schedule.get('execution_time', '')
            if is_time_in_window(execution_time, current_time_str, future_time_str):
                time_matched_schedules.append(schedule)
                logger.debug(f"  ✓ Strategy {schedule.get('strategy_id')} at {execution_time} within window")

        if not time_matched_schedules:
            logger.info(f"No strategies in time window {current_time_str}-{future_time_str}")
            return []

        logger.info(f"⏱️ {len(time_matched_schedules)} strategies within time window")

        # Phase 2: Filter by broker allocation
        # Get unique basket_ids and check which have allocation for this client_id
        basket_ids = set(s.get('basket_id') for s in time_matched_schedules if s.get('basket_id'))

        if not basket_ids:
            logger.warning("No basket_ids found in matched schedules")
            return []

        # Check allocations for each basket
        allocated_baskets = set()
        for basket_id in basket_ids:
            if has_broker_allocation(basket_id, client_id):
                allocated_baskets.add(basket_id)
                logger.debug(f"  ✓ Basket {basket_id} has allocation for client {client_id}")
            else:
                logger.debug(f"  ✗ Basket {basket_id} has NO allocation for client {client_id}")

        if not allocated_baskets:
            logger.info(f"No baskets have allocation for client_id {client_id}")
            return []

        # Filter strategies to only those with broker allocation
        broker_strategies = [
            s for s in time_matched_schedules
            if s.get('basket_id') in allocated_baskets
        ]

        logger.info(f"🏦 {len(broker_strategies)} strategies have allocation for client {client_id}")

        return broker_strategies

    except Exception as e:
        logger.error(f"Error querying strategies for entry: {str(e)}")
        return []


def query_basket_allocations(basket_id: str) -> List[Dict]:
    """
    Query all broker allocations for a basket using AllocationsByBasket GSI.
    Results are cached for the duration of the Lambda invocation.

    Args:
        basket_id: Basket identifier

    Returns:
        List of allocation items for the basket
    """
    global _allocation_cache

    # Return cached result if available
    if basket_id in _allocation_cache:
        return _allocation_cache[basket_id]

    try:
        table = dynamodb.Table(os.environ['TRADING_CONFIGURATIONS_TABLE'])

        response = table.query(
            IndexName='AllocationsByBasket',
            KeyConditionExpression='basket_id = :basket_id AND begins_with(entity_type_priority, :prefix)',
            ExpressionAttributeValues={
                ':basket_id': basket_id,
                ':prefix': 'BASKET_ALLOCATION#'
            },
            ProjectionExpression='allocation_id, client_id, broker_name, lot_multiplier, priority, max_lots_per_order, #status, risk_limit_per_trade',
            ExpressionAttributeNames={'#status': 'status'}
        )

        allocations = response.get('Items', [])
        _allocation_cache[basket_id] = allocations

        logger.debug(f"Queried {len(allocations)} allocations for basket {basket_id}")
        return allocations

    except Exception as e:
        logger.error(f"Error querying basket allocations: {str(e)}")
        _allocation_cache[basket_id] = []
        return []


def has_broker_allocation(basket_id: str, client_id: str) -> bool:
    """
    Check if a basket has an active allocation for the specified client_id.

    Args:
        basket_id: Basket identifier
        client_id: Broker client ID to check

    Returns:
        True if basket has active allocation for client_id
    """
    allocations = query_basket_allocations(basket_id)

    for alloc in allocations:
        if alloc.get('client_id') == client_id:
            status = alloc.get('status', '').upper()
            if status == 'ACTIVE':
                return True

    return False


def get_allocation_for_broker(basket_id: str, client_id: str) -> Optional[Dict]:
    """
    Get the specific allocation details for a broker/client in a basket.

    Args:
        basket_id: Basket identifier
        client_id: Broker client ID

    Returns:
        Allocation dict if found and active, None otherwise
    """
    allocations = query_basket_allocations(basket_id)

    for alloc in allocations:
        if alloc.get('client_id') == client_id:
            status = alloc.get('status', '').upper()
            if status == 'ACTIVE':
                # Convert Decimal to float for JSON serialization
                return {
                    'allocation_id': alloc.get('allocation_id'),
                    'client_id': alloc.get('client_id'),
                    'broker_name': alloc.get('broker_name'),
                    'lot_multiplier': float(alloc.get('lot_multiplier', 1)) if isinstance(alloc.get('lot_multiplier'), Decimal) else alloc.get('lot_multiplier', 1),
                    'priority': int(alloc.get('priority', 1)) if isinstance(alloc.get('priority'), Decimal) else alloc.get('priority', 1),
                    'max_lots_per_order': float(alloc.get('max_lots_per_order')) if alloc.get('max_lots_per_order') and isinstance(alloc.get('max_lots_per_order'), Decimal) else alloc.get('max_lots_per_order'),
                    'risk_limit_per_trade': float(alloc.get('risk_limit_per_trade')) if alloc.get('risk_limit_per_trade') and isinstance(alloc.get('risk_limit_per_trade'), Decimal) else alloc.get('risk_limit_per_trade')
                }

    return None


def is_time_in_window(check_time: str, window_start: str, window_end: str) -> bool:
    """
    Check if a time string (HH:MM) is within the specified window.

    Handles midnight crossing (e.g., 23:58 to 00:02).

    Args:
        check_time: Time to check in HH:MM format
        window_start: Window start time in HH:MM format
        window_end: Window end time in HH:MM format

    Returns:
        True if check_time is within the window
    """
    try:
        if not check_time:
            return False

        # Handle normal case (no midnight crossing)
        if window_start <= window_end:
            return window_start <= check_time <= window_end

        # Handle midnight crossing (e.g., 23:58 to 00:02)
        # Time is valid if it's >= start OR <= end
        return check_time >= window_start or check_time <= window_end

    except Exception:
        return False


def emit_strategy_execution_event(
    user_id: str,
    strategy: Dict,
    execution_type: str,
    weekday: str,
    broker_context: Dict,
    allocation: Optional[Dict]
) -> Dict:
    """
    Emit a Strategy Execution Event to EventBridge.

    The event includes pre-fetched allocation data so the executor
    only needs to fetch strategy details (legs, underlying, etc.).

    Args:
        user_id: User identifier
        strategy: Strategy schedule data (from UserScheduleDiscovery GSI)
        execution_type: ENTRY or EXIT
        weekday: Current weekday abbreviation (MON, TUE, etc.)
        broker_context: Broker details (broker_id, client_id, broker_name, broker_config)
        allocation: Pre-fetched allocation data for this broker

    Returns:
        Result dict with status and event_id
    """
    strategy_id = strategy.get('strategy_id')
    basket_id = strategy.get('basket_id')
    execution_time = strategy.get('execution_time')

    try:
        execution_event_id = str(uuid.uuid4())

        # Build event detail with pre-fetched allocation
        event_detail = {
            # Execution identifiers
            'execution_event_id': execution_event_id,
            'user_id': user_id,
            'strategy_id': strategy_id,
            'basket_id': basket_id,
            'execution_type': execution_type,
            'execution_time': execution_time,
            'weekday': weekday,

            # Broker context
            'broker_id': broker_context.get('broker_id'),
            'client_id': broker_context.get('client_id'),
            'broker_name': broker_context.get('broker_name'),
            'broker_config': broker_context.get('broker_config'),

            # Pre-fetched allocation data (executor won't re-query)
            'allocation': allocation,

            # Metadata
            'source': 'strategy_entry_handler',
            'emitted_at': datetime.now(timezone.utc).isoformat(),

            # Flag for executor to know allocation is pre-loaded
            'allocation_preloaded': True
        }

        # Emit to EventBridge
        response = eventbridge_client.put_events(
            Entries=[
                {
                    'Source': 'qlalgo.options.trading',
                    'DetailType': 'Strategy.Execution.Triggered',
                    'Detail': json.dumps(event_detail, cls=DecimalEncoder),
                    'Time': datetime.now(timezone.utc)
                }
            ]
        )

        # Check for failures
        if response.get('FailedEntryCount', 0) > 0:
            error_msg = response['Entries'][0].get('ErrorMessage', 'Unknown error')
            logger.error(f"❌ Failed to emit execution event for strategy {strategy_id}: {error_msg}")
            return {
                'strategy_id': strategy_id,
                'basket_id': basket_id,
                'broker_name': broker_context.get('broker_name'),
                'client_id': broker_context.get('client_id'),
                'status': 'FAILED',
                'error': error_msg
            }

        eventbridge_event_id = response['Entries'][0].get('EventId')
        logger.info(f"📤 Emitted execution event for strategy {strategy_id} on broker {broker_context.get('broker_name')}")

        return {
            'strategy_id': strategy_id,
            'basket_id': basket_id,
            'broker_name': broker_context.get('broker_name'),
            'client_id': broker_context.get('client_id'),
            'execution_time': execution_time,
            'status': 'EMITTED',
            'execution_event_id': execution_event_id,
            'eventbridge_event_id': eventbridge_event_id
        }

    except Exception as e:
        logger.error(f"❌ Error emitting execution event for strategy {strategy_id}: {str(e)}")
        return {
            'strategy_id': strategy_id,
            'basket_id': basket_id,
            'status': 'ERROR',
            'error': str(e)
        }


def create_success_response(
    user_id: str,
    sub_event_id: str,
    count: int,
    results: List,
    broker_id: str = None,
    client_id: str = None,
    message: str = None
) -> Dict:
    """Create standardized success response."""
    body = {
        'success': True,
        'user_id': user_id,
        'sub_event_id': sub_event_id,
        'strategies_emitted': count,
        'results': results
    }

    if broker_id:
        body['broker_id'] = broker_id
    if client_id:
        body['client_id'] = client_id
    if message:
        body['message'] = message

    return {
        'statusCode': 200,
        'body': json.dumps(body, cls=DecimalEncoder)
    }


def create_error_response(error: str) -> Dict:
    """Create standardized error response."""
    return {
        'statusCode': 500,
        'body': json.dumps({
            'success': False,
            'error': error
        })
    }
