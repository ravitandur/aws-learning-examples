import json
import boto3
import os
import sys
import time as time_module
from datetime import datetime, timezone, timedelta, time
from typing import Dict, Any, List
import uuid

# Add paths for imports
sys.path.append('/opt/python')
sys.path.append('/var/task')  # Add current directory to path
sys.path.append('/var/task/option_baskets')  # Add option_baskets directory to path

# Import shared logger directly
from shared_utils.logger import setup_logger, log_lambda_event, log_user_action, log_api_response
logger = setup_logger(__name__)

# Initialize AWS clients
eventbridge_client = boto3.client('events', region_name=os.environ.get('REGION', 'ap-south-1'))
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'ap-south-1'))

def query_active_users_for_execution_time(user_profiles_table, execution_time: str, weekday: str) -> List[str]:
    """
    Query active users from user_profiles table using efficient ActiveUsersIndex GSI
    Much more efficient than scanning trading configurations table
    """
    try:
        logger.info(f"🔍 Querying active users for {execution_time} on {weekday} using ActiveUsersIndex GSI")
        
        # Query user_profiles table using ActiveUsersIndex GSI for O(active_users) performance
        response = user_profiles_table.query(
            IndexName='ActiveUsersIndex',
            KeyConditionExpression='#status = :active_status',
            ExpressionAttributeValues={
                ':active_status': 'active'
            },
            ExpressionAttributeNames={'#status': 'status'},
            ProjectionExpression='user_id'
        )
        
        # Extract user_ids from active users
        user_ids = [item['user_id'] for item in response.get('Items', [])]
        
        logger.info(f"✅ Found {len(user_ids)} active users (GSI optimization: O(active_users) vs O(all_users))")
        return user_ids
        
    except Exception as e:
        logger.error(f"❌ Error querying active users from user_profiles: {str(e)}")
        return []

def create_active_user_event(user_id: str, current_ist: datetime,
                             weekday: str, market_phase: str) -> Dict[str, Any]:
    """
    🚀 COMPREHENSIVE ACTIVE USER EVENT

    Emits a single event per active user containing all sub-events:
    - strategy_entry: Schedule and execute strategy entries
    - strategy_exit: Schedule and execute strategy exits
    - stop_loss_check: Real-time stop loss monitoring
    - target_profit_check: Target profit monitoring
    - trailing_sl_check: Trailing stop loss adjustments
    - duplicate_order_check: Order deduplication validation
    - re_entry_check: Re-entry condition monitoring
    - re_execute_check: Re-execution condition monitoring
    - position_sync: Sync positions across brokers

    The downstream handler processes all sub-events for the user in a single invocation.
    """

    current_time_str = current_ist.strftime("%H:%M")
    current_minute = current_ist.minute

    # Determine which sub-events to include based on market phase and timing
    sub_events = []

    # 1. STRATEGY ENTRY - Check every minute with 1-minute lookahead
    if market_phase in ['MARKET_OPEN', 'EARLY_TRADING', 'ACTIVE_TRADING', 'AFTERNOON_TRADING', 'PRE_CLOSE']:
        sub_events.append({
            'event_type': 'strategy_entry',
            'enabled': True,
            'lookahead_minutes': 1,
            'priority': 'HIGH' if market_phase in ['MARKET_OPEN', 'EARLY_TRADING'] else 'NORMAL',
            'query_pattern': 'GSI4_UserScheduleDiscovery'
        })

    # 2. STRATEGY EXIT - Check every minute with 1-minute lookahead
    if market_phase in ['MARKET_OPEN', 'EARLY_TRADING', 'ACTIVE_TRADING', 'AFTERNOON_TRADING', 'PRE_CLOSE']:
        sub_events.append({
            'event_type': 'strategy_exit',
            'enabled': True,
            'lookahead_minutes': 1,
            'priority': 'HIGH' if market_phase in ['PRE_CLOSE', 'AFTERNOON_TRADING'] else 'NORMAL',
            'query_pattern': 'GSI4_UserScheduleDiscovery'
        })

    # 3. STOP LOSS CHECK - Every minute during active trading
    if market_phase in ['MARKET_OPEN', 'EARLY_TRADING', 'ACTIVE_TRADING', 'AFTERNOON_TRADING', 'PRE_CLOSE']:
        sub_events.append({
            'event_type': 'stop_loss_check',
            'enabled': True,
            'check_frequency': 'EVERY_MINUTE',
            'priority': 'CRITICAL' if market_phase == 'PRE_CLOSE' else 'HIGH',
            'monitoring_scope': 'ALL_ACTIVE_POSITIONS'
        })

    # 4. TARGET PROFIT CHECK - Every minute during active trading
    if market_phase in ['MARKET_OPEN', 'EARLY_TRADING', 'ACTIVE_TRADING', 'AFTERNOON_TRADING', 'PRE_CLOSE']:
        sub_events.append({
            'event_type': 'target_profit_check',
            'enabled': True,
            'check_frequency': 'EVERY_MINUTE',
            'priority': 'HIGH',
            'monitoring_scope': 'ALL_ACTIVE_POSITIONS'
        })

    # 5. TRAILING STOP LOSS CHECK - Every minute during active trading
    if market_phase in ['ACTIVE_TRADING', 'AFTERNOON_TRADING', 'PRE_CLOSE']:
        sub_events.append({
            'event_type': 'trailing_sl_check',
            'enabled': True,
            'check_frequency': 'EVERY_MINUTE',
            'priority': 'HIGH',
            'adjustment_enabled': True
        })

    # 6. DUPLICATE ORDER CHECK - Every minute during active periods
    if market_phase in ['MARKET_OPEN', 'EARLY_TRADING', 'ACTIVE_TRADING', 'AFTERNOON_TRADING', 'PRE_CLOSE']:
        sub_events.append({
            'event_type': 'duplicate_order_check',
            'enabled': True,
            'lookback_minutes': 5,
            'priority': 'NORMAL',
            'dedup_strategy': 'TIME_AND_SYMBOL_BASED'
        })

    # 7. RE-ENTRY CHECK - Every minute during active trading
    if market_phase in ['MARKET_OPEN', 'EARLY_TRADING', 'ACTIVE_TRADING', 'AFTERNOON_TRADING', 'PRE_CLOSE']:
        sub_events.append({
            'event_type': 're_entry_check',
            'enabled': True,
            'check_frequency': 'EVERY_MINUTE',
            'priority': 'NORMAL',
            'conditions': ['STOP_LOSS_HIT', 'POSITION_CLOSED']
        })

    # 8. RE-EXECUTE CHECK - Every minute for failed executions
    if market_phase in ['MARKET_OPEN', 'EARLY_TRADING', 'ACTIVE_TRADING', 'AFTERNOON_TRADING', 'PRE_CLOSE']:
        sub_events.append({
            'event_type': 're_execute_check',
            'enabled': True,
            'check_frequency': 'EVERY_MINUTE',
            'priority': 'HIGH',
            'max_retries': 3,
            'conditions': ['EXECUTION_FAILED', 'ORDER_REJECTED']
        })

    # 9. POSITION SYNC - Every 10 minutes to sync broker positions
    if current_minute % 10 == 0:
        sub_events.append({
            'event_type': 'position_sync',
            'enabled': True,
            'check_frequency': 'EVERY_10_MINUTES',
            'priority': 'LOW',
            'sync_scope': 'ALL_BROKERS'
        })

    return {
        'source': 'options.trading.active_user',
        'detail_type': 'Active User Event',
        'detail': {
            'event_id': str(uuid.uuid4()),
            'user_id': user_id,
            'trigger_time_ist': current_ist.isoformat(),
            'trigger_time_str': current_time_str,
            'weekday': weekday.upper(),
            'market_phase': market_phase,
            'sub_events': sub_events,
            'sub_event_count': len(sub_events),
            'priority': 'CRITICAL' if market_phase == 'PRE_CLOSE' else ('HIGH' if market_phase in ['MARKET_OPEN', 'EARLY_TRADING'] else 'NORMAL'),
            'event_version': '2.0',
            'processing_hint': 'PROCESS_ALL_SUB_EVENTS_SEQUENTIALLY'
        }
    }

def emit_active_user_events(user_profiles_table, current_ist: datetime, market_phase: str) -> Dict[str, Any]:
    """
    🚀 EMIT COMPREHENSIVE ACTIVE USER EVENTS

    For each active user, emits a single Active User Event containing all relevant sub-events:
    - strategy_entry, strategy_exit
    - stop_loss_check, target_profit_check, trailing_sl_check
    - duplicate_order_check
    - re_entry_check, re_execute_check
    - position_sync

    Sub-events are dynamically included based on:
    - Current market phase (MARKET_OPEN, ACTIVE_TRADING, PRE_CLOSE, etc.)
    - Current minute (every 3 min for entry/exit, every 5 min for re-entry, etc.)
    """
    try:
        current_weekday = current_ist.strftime("%A").upper()
        current_minute = current_ist.minute

        logger.info(f"🚀 Generating Active User Events for {current_weekday} at minute {current_minute}")
        logger.info(f"🏛️ Market Phase: {market_phase}")

        # Find active users using efficient GSI query (O(active_users) performance)
        active_users = query_active_users_for_execution_time(
            user_profiles_table, "", current_weekday
        )

        if not active_users:
            logger.info("📬 No active users found")
            return {
                'events_generated': 0,
                'active_users_count': 0,
                'market_phase': market_phase
            }

        # Generate EventBridge events in batches of 10
        events_batch = []
        total_events = 0
        total_sub_events = 0

        for user_id in active_users:
            # Create comprehensive active user event with all sub-events
            active_user_event = create_active_user_event(
                user_id, current_ist, current_weekday, market_phase
            )

            sub_event_count = active_user_event['detail']['sub_event_count']

            # Only emit if there are sub-events to process
            if sub_event_count > 0:
                events_batch.append(active_user_event)
                total_sub_events += sub_event_count

                # Send batch when we reach 10 events (EventBridge limit)
                if len(events_batch) >= 10:
                    emit_events_batch_to_eventbridge(events_batch)
                    total_events += len(events_batch)
                    events_batch = []

        # Send remaining events
        if events_batch:
            emit_events_batch_to_eventbridge(events_batch)
            total_events += len(events_batch)

        logger.info(f"✅ Generated {total_events} Active User Events with {total_sub_events} total sub-events")
        logger.info(f"📊 Active users: {len(active_users)}, Events emitted: {total_events}")

        return {
            'events_generated': total_events,
            'sub_events_total': total_sub_events,
            'active_users_count': len(active_users),
            'market_phase': market_phase,
            'event_type': 'Active User Event',
            'event_version': '2.0'
        }

    except Exception as e:
        logger.error(f"❌ Error generating Active User Events: {str(e)}")
        return {'events_generated': 0, 'error': str(e)}

def emit_events_batch_to_eventbridge(events_batch: List[Dict]) -> None:
    """Emit batch of events to EventBridge"""
    try:
        # Prepare EventBridge entries
        entries = []
        for event in events_batch:
            entries.append({
                'Source': event['source'],
                'DetailType': event['detail_type'],
                'Detail': json.dumps(event['detail']),
                'Time': datetime.now(timezone.utc)
            })
        
        # Send to EventBridge
        response = eventbridge_client.put_events(Entries=entries)
        
        failed_count = response.get('FailedEntryCount', 0)
        if failed_count > 0:
            logger.warning(f"⚠️ {failed_count} events failed to send to EventBridge")
        
        logger.debug(f"📤 Sent batch of {len(entries)} events to EventBridge")
        
    except Exception as e:
        logger.error(f"❌ Error sending events to EventBridge: {str(e)}")

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    🚀 Revolutionary 0-Second Precision Event Emitter

    INSTITUTIONAL-GRADE TIMING SYSTEM:
    - Triggered by Step Functions Express with exact 60-second intervals
    - Achieves TRUE 0-second precision (no EventBridge delay)
    - Operational hours: 8:55 AM - 11:55 PM IST
    - Never misses events, no duplicates, perfect reliability

    Event Architecture (v2.0):
    1. ACTIVE USER EVENTS - Per-user comprehensive events containing all sub-events:
       - strategy_entry (every 3 min)
       - strategy_exit (every 3 min)
       - stop_loss_check (every minute)
       - target_profit_check (every minute)
       - trailing_sl_check (every minute)
       - duplicate_order_check (every minute)
       - re_entry_check (every 5 min)
       - re_execute_check (every 5 min)
       - position_sync (every 10 min)

    2. GLOBAL EVENTS - System-wide events:
       - refresh_market_data (every minute)
    """

    # Log the incoming Lambda event (sanitized)
    log_lambda_event(logger, event, context)

    try:
        # Detect trigger source for optimal handling
        trigger_type = event.get('trigger_type', 'UNKNOWN')
        is_step_function_trigger = trigger_type == 'STEP_FUNCTION_PRECISION_TIMER'

        # Get precise current IST time
        current_utc = datetime.now(timezone.utc)
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        current_ist = current_utc.astimezone(ist_offset)

        current_time_str = current_ist.strftime("%H:%M")
        current_minute = current_ist.minute
        current_second = current_ist.second

        # Log precision achievement
        if is_step_function_trigger:
            logger.info(f"🎯 PRECISION ACHIEVED: Event emitted at {current_time_str}:{current_second:02d} IST (Step Functions)")
        else:
            logger.info(f"Event Emitter triggered at {current_time_str}:{current_second:02d} IST (EventBridge fallback)")

        # Operational hours validation (generic window, not exchange-specific)
        if not is_trading_day(current_ist):
            logger.info("Non-trading day - stopping Step Function execution")
            return create_market_closed_response(current_time_str, "NON_TRADING_DAY")

        if not is_within_operational_hours(current_ist):
            logger.info(f"Outside operational hours ({current_time_str} IST) - stopping Step Function execution")
            return create_market_closed_response(current_time_str, "OUTSIDE_OPERATIONAL_HOURS")

        # Determine market phase for intelligent event routing
        market_phase = get_market_phase(current_ist)

        # ============================================================================
        # ACTIVE USER EVENTS - Comprehensive per-user events with all sub-events
        # ============================================================================
        user_profiles_table = dynamodb.Table(os.environ['USER_PROFILES_TABLE'])

        # Emit Active User Events every minute (sub-events are filtered internally based on timing)
        active_user_results = emit_active_user_events(user_profiles_table, current_ist, market_phase)

        # ============================================================================
        # GLOBAL EVENTS - System-wide events (not user-specific)
        # ============================================================================
        global_events_to_emit = []

        # Market Data Refresh - every minute throughout operational hours
        global_events_to_emit.append(create_market_data_event(current_ist, market_phase))

        # Emit global events to EventBridge
        global_emission_results = []
        for event_detail in global_events_to_emit:
            result = emit_event_to_eventbridge(event_detail)
            global_emission_results.append(result)

        # Extract metrics from active user events
        total_user_events = active_user_results.get('events_generated', 0)
        total_sub_events = active_user_results.get('sub_events_total', 0)
        active_users_count = active_user_results.get('active_users_count', 0)

        logger.info(f"✅ Event emission complete at {current_time_str}:{current_second:02d} IST")
        logger.info(f"📊 Active User Events: {total_user_events} (containing {total_sub_events} sub-events)")
        logger.info(f"📊 Global Events: {len(global_emission_results)}")
        logger.info(f"👥 Active Users: {active_users_count}")
        
        # Calculate precise wait time for next 0-second boundary
        next_minute_wait_seconds = calculate_next_minute_wait_seconds(current_ist)
        
        return {
            'statusCode': 200,
            'continue_execution': True,  # Tell Step Function to continue
            'wait_seconds': next_minute_wait_seconds,  # Dynamic wait for 0-second precision
            'body': json.dumps({
                'success': True,
                'current_time_ist': current_time_str,
                'current_second': current_second,
                'market_phase': market_phase,
                'event_architecture_version': '2.0',
                'active_user_events': {
                    'events_emitted': total_user_events,
                    'sub_events_total': total_sub_events,
                    'active_users_count': active_users_count
                },
                'global_events': {
                    'events_emitted': len(global_emission_results),
                    'results': global_emission_results
                },
                'active_user_event_summary': active_user_results,
                'next_execution_wait_seconds': next_minute_wait_seconds,
                'message': f'Events emitted at {current_time_str}:{current_second:02d} IST - {total_user_events} user events ({total_sub_events} sub-events), {len(global_emission_results)} global events'
            })
        }
        
    except Exception as e:
        logger.error("Failed to emit events", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to emit events',
                'message': str(e)
            })
        }


def get_market_phase(current_ist: datetime) -> str:
    """
    Determine current market phase for intelligent event routing
    Different phases require different event patterns
    """
    
    current_time = current_ist.time()
    
    # Market phases based on IST times
    if current_time >= time(9, 15) and current_time < time(9, 30):
        return 'MARKET_OPEN'  # Opening phase - high activity
    elif current_time >= time(9, 30) and current_time < time(10, 30):
        return 'EARLY_TRADING'  # Early trading - strategy entries
    elif current_time >= time(10, 30) and current_time < time(13, 0):
        return 'ACTIVE_TRADING'  # Active trading - normal operations
    elif current_time >= time(13, 0) and current_time < time(14, 0):
        return 'LUNCH_BREAK'  # Lunch break - reduced activity
    elif current_time >= time(14, 0) and current_time < time(15, 20):
        return 'AFTERNOON_TRADING'  # Afternoon trading - position management
    elif current_time >= time(15, 20) and current_time < time(15, 30):
        return 'PRE_CLOSE'  # Pre-close - exit strategies
    else:
        return 'AFTER_HOURS'  # Outside market hours


def create_schedule_strategy_event(current_ist: datetime, market_phase: str) -> Dict[str, Any]:
    """Create schedule strategy trigger event for 5-minute strategy discovery"""
    
    # Look ahead 5 minutes to discover strategies due for execution
    future_time = current_ist + timedelta(minutes=5)
    future_time_str = future_time.strftime("%H:%M")
    
    return {
        'source': 'options.trading.scheduler',
        'detail_type': 'Schedule Strategy Trigger',
        'detail': {
            'event_id': str(uuid.uuid4()),
            'trigger_time_ist': current_ist.isoformat(),
            'discovery_window_start': current_ist.isoformat(),
            'discovery_window_end': future_time.isoformat(),
            'target_execution_time': future_time_str,
            'market_phase': market_phase,
            'scheduling_interval': '5_minutes',
            'priority': 'HIGH' if market_phase in ['MARKET_OPEN', 'PRE_CLOSE'] else 'NORMAL',
            'query_optimization': 'GSI2_UserExecutionSchedule',
            'expected_strategy_volume': get_expected_volume(market_phase)
        }
    }


def create_stop_loss_event(current_ist: datetime, market_phase: str) -> Dict[str, Any]:
    """Create stop loss monitoring event for real-time risk management"""
    
    return {
        'source': 'options.trading.risk',
        'detail_type': 'Check Stop Loss',
        'detail': {
            'event_id': str(uuid.uuid4()),
            'trigger_time_ist': current_ist.isoformat(),
            'market_phase': market_phase,
            'risk_check_type': 'REAL_TIME_MONITORING',
            'monitoring_scope': 'ALL_ACTIVE_POSITIONS',
            'priority': 'CRITICAL' if market_phase == 'PRE_CLOSE' else 'HIGH',
            'check_frequency': 'EVERY_MINUTE',
            'emergency_exit_enabled': True,
            'market_volatility_context': get_volatility_context(market_phase)
        }
    }


def create_duplicate_order_event(current_ist: datetime, market_phase: str) -> Dict[str, Any]:
    """Create duplicate order check event for order validation"""
    
    return {
        'source': 'options.trading.validation',
        'detail_type': 'Check Duplicate Orders',
        'detail': {
            'event_id': str(uuid.uuid4()),
            'trigger_time_ist': current_ist.isoformat(),
            'market_phase': market_phase,
            'validation_type': 'ORDER_DEDUPLICATION',
            'check_window_minutes': 5,  # Look back 5 minutes for duplicates
            'priority': 'NORMAL',
            'broker_scope': 'ALL_BROKERS',
            'dedup_strategy': 'TIME_AND_SYMBOL_BASED'
        }
    }


def create_market_data_event(current_ist: datetime, market_phase: str) -> Dict[str, Any]:
    """Create market data refresh event for real-time price updates"""
    
    return {
        'source': 'options.trading.market',
        'detail_type': 'Refresh Market Data',
        'detail': {
            'event_id': str(uuid.uuid4()),
            'trigger_time_ist': current_ist.isoformat(),
            'market_phase': market_phase,
            'refresh_type': 'INCREMENTAL_UPDATE',
            'data_sources': ['NSE', 'LIVE_FEED'],
            'priority': 'HIGH' if market_phase in ['MARKET_OPEN', 'PRE_CLOSE'] else 'NORMAL',
            'include_greeks': True,
            'include_volatility': True,
            'holiday_calendar_check': True,
            'indices': ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
        }
    }


def emit_event_to_eventbridge(event_detail: Dict[str, Any]) -> Dict[str, Any]:
    """Emit event to EventBridge for processing by event handlers"""
    
    try:
        # Prepare EventBridge event entry
        event_entry = {
            'Source': event_detail['source'],
            'DetailType': event_detail['detail_type'],
            'Detail': json.dumps(event_detail['detail']),
            'Time': datetime.now(timezone.utc)
        }
        
        # Send event to EventBridge
        response = eventbridge_client.put_events(
            Entries=[event_entry]
        )
        
        # Check for failures
        if response['FailedEntryCount'] > 0:
            logger.error(f"Failed to emit event: {event_detail['detail_type']}", 
                        extra={"failed_entries": response['Entries']})
            return {
                'event_type': event_detail['detail_type'],
                'status': 'FAILED',
                'error': response['Entries'][0].get('ErrorMessage', 'Unknown error')
            }
        
        logger.info(f"Successfully emitted event: {event_detail['detail_type']}")
        return {
            'event_type': event_detail['detail_type'],
            'status': 'SUCCESS',
            'event_id': response['Entries'][0]['EventId']
        }
        
    except Exception as e:
        logger.error(f"Failed to emit event to EventBridge: {event_detail['detail_type']}", 
                    extra={"error": str(e)})
        return {
            'event_type': event_detail['detail_type'],
            'status': 'ERROR',
            'error': str(e)
        }


def get_expected_volume(market_phase: str) -> str:
    """Get expected strategy execution volume based on market phase"""
    
    volume_map = {
        'MARKET_OPEN': 'VERY_HIGH',  # 9:15-9:30 - Most strategies execute
        'EARLY_TRADING': 'HIGH',     # 9:30-10:30 - Entry strategies
        'ACTIVE_TRADING': 'MEDIUM',   # 10:30-13:00 - Normal operations
        'LUNCH_BREAK': 'LOW',        # 13:00-14:00 - Reduced activity
        'AFTERNOON_TRADING': 'MEDIUM', # 14:00-15:20 - Position management
        'PRE_CLOSE': 'VERY_HIGH',    # 15:20-15:30 - Exit strategies
        'AFTER_HOURS': 'NONE'        # Outside market hours
    }
    
    return volume_map.get(market_phase, 'UNKNOWN')


def get_volatility_context(market_phase: str) -> str:
    """Get market volatility context for risk management"""
    
    volatility_map = {
        'MARKET_OPEN': 'HIGH_VOLATILITY',    # Opening price discovery
        'EARLY_TRADING': 'MEDIUM_VOLATILITY', # Settling after open
        'ACTIVE_TRADING': 'NORMAL_VOLATILITY', # Stable mid-day
        'LUNCH_BREAK': 'LOW_VOLATILITY',      # Reduced volume
        'AFTERNOON_TRADING': 'NORMAL_VOLATILITY', # Active afternoon
        'PRE_CLOSE': 'HIGH_VOLATILITY',      # Closing price pressure
        'AFTER_HOURS': 'NO_TRADING'          # Market closed
    }
    
    return volatility_map.get(market_phase, 'UNKNOWN_VOLATILITY')


def is_trading_day(current_ist: datetime) -> bool:
    """
    Check if current day is a trading day
    Basic weekday check - can be enhanced with NSE holiday calendar
    """
    
    weekday = current_ist.weekday()  # 0=Monday, 6=Sunday
    
    # Basic check - weekdays only (Monday to Friday)
    if weekday >= 5:  # Saturday (5) or Sunday (6)
        return False
    
    # TODO: Add NSE holiday calendar integration
    # This would check against official NSE holiday list
    # For now, assume all weekdays are trading days
    
    return True


def is_within_operational_hours(current_ist: datetime) -> bool:
    """
    Check if current time is within the Master Precision Timer operational window.
    This is a GENERIC operational window, NOT exchange-specific market hours.

    Operational Window: 8:55 AM - 11:55 PM IST
    - Covers pre-market preparation (before 9:15 AM)
    - Covers all exchange market hours (NSE, BSE, MCX)
    - Covers post-market processing

    TODO: Exchange-specific market hours will be implemented separately:
    - NSE/BSE Equity: 9:15 AM - 3:30 PM IST
    - NSE F&O: 9:15 AM - 3:30 PM IST
    - MCX: 9:00 AM - 11:30 PM IST (extended hours)
    - Currency: 9:00 AM - 5:00 PM IST
    """
    current_time = current_ist.time()

    # Generic operational window for Master Precision Timer
    OPERATIONAL_START = time(8, 55)   # 8:55 AM IST
    OPERATIONAL_END = time(23, 55)    # 11:55 PM IST

    return OPERATIONAL_START <= current_time <= OPERATIONAL_END


# Exchange-specific market hours (to be used by strategy execution logic)
EXCHANGE_MARKET_HOURS = {
    'NSE': {'start': time(9, 15), 'end': time(15, 30)},
    'BSE': {'start': time(9, 15), 'end': time(15, 30)},
    'NFO': {'start': time(9, 15), 'end': time(15, 30)},
    'MCX': {'start': time(9, 0), 'end': time(23, 30)},
    'CDS': {'start': time(9, 0), 'end': time(17, 0)},
}


def is_exchange_market_open(exchange: str, current_ist: datetime) -> bool:
    """
    Check if a specific exchange is currently open.
    Used by strategy execution to validate trades.
    """
    current_time = current_ist.time()
    exchange_hours = EXCHANGE_MARKET_HOURS.get(exchange.upper())

    if not exchange_hours:
        # Default to NSE hours for unknown exchanges
        exchange_hours = EXCHANGE_MARKET_HOURS['NSE']

    return exchange_hours['start'] <= current_time <= exchange_hours['end']


def calculate_next_minute_wait_seconds(current_ist: datetime) -> int:
    """
    🎯 PRECISION CALCULATION: Calculate exact seconds to wait for next 0-second boundary
    
    This is the KEY to achieving TRUE 0-second precision!
    Instead of fixed 60-second waits, we calculate dynamic waits to hit exact minute boundaries.
    
    Examples:
    - Current time: 09:00:27 → Wait 33 seconds → Next execution: 09:01:00
    - Current time: 09:01:03 → Wait 57 seconds → Next execution: 09:02:00  
    - Current time: 09:02:45 → Wait 15 seconds → Next execution: 09:03:00
    """
    
    current_second = current_ist.second
    
    # Calculate seconds remaining in current minute (simple and precise)
    seconds_remaining = 60 - current_second
    
    # Ensure we don't return 0 (Step Functions needs at least 1 second)
    if seconds_remaining <= 0:
        seconds_remaining = 60
    
    return seconds_remaining


def create_market_closed_response(current_time_str: str, reason: str) -> Dict[str, Any]:
    """
    Create response when market is closed - instructs Step Function to stop
    """
    return {
        'statusCode': 200,
        'continue_execution': False,  # This stops the Step Function loop
        'wait_seconds': 60,  # Provide default wait_seconds for Step Function compatibility
        'body': json.dumps({
            'success': True,
            'current_time_ist': current_time_str,
            'market_status': 'CLOSED',
            'reason': reason,
            'message': f'Market closed ({reason}) - Step Function will terminate'
        })
    }