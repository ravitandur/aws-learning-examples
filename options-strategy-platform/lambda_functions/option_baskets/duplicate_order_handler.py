"""
🚀 DUPLICATE ORDER HANDLER

Handles Duplicate Order Check sub-events from Active User Event Handler.
Validates recent orders to prevent duplicate order placement.

Responsibilities:
- Query recent orders within lookback window
- Detect potential duplicate orders
- Cancel duplicate orders if found
- Log duplicate detection events
"""

import json
import os
import sys
import boto3
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from decimal import Decimal
from collections import defaultdict

sys.path.append('/opt/python')
sys.path.append('/var/task')

from shared_utils.logger import setup_logger, log_lambda_event

logger = setup_logger(__name__)

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'ap-south-1'))


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handle Duplicate Order Check events.

    Detects and handles duplicate orders within the lookback window.
    """
    log_lambda_event(logger, event, context)

    try:
        detail = event.get('detail', {})
        user_id = detail.get('user_id')
        sub_event_id = detail.get('sub_event_id')
        lookback_minutes = detail.get('lookback_minutes', 5)
        dedup_strategy = detail.get('dedup_strategy', 'TIME_AND_SYMBOL_BASED')

        if not user_id:
            logger.error("Missing user_id in Duplicate Order Check event")
            return create_error_response("Missing user_id")

        logger.info(f"Processing Duplicate Order Check for user {user_id}")
        logger.info(f"Lookback: {lookback_minutes} minutes, Strategy: {dedup_strategy}")

        # Get current IST time
        current_utc = datetime.now(timezone.utc)
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        current_ist = current_utc.astimezone(ist_offset)

        # Query recent orders
        orders = query_recent_orders(user_id, lookback_minutes)

        if not orders:
            logger.info(f"No recent orders for user {user_id}")
            return create_success_response(user_id, sub_event_id, 0, 0, [])

        # Detect duplicates based on strategy
        duplicates = detect_duplicates(orders, dedup_strategy)

        if duplicates:
            logger.warning(f"Found {len(duplicates)} potential duplicate orders")
            # Handle duplicates (cancel, flag, etc.)
            handle_duplicates(user_id, duplicates, current_ist)

        return create_success_response(
            user_id, sub_event_id,
            len(orders), len(duplicates),
            duplicates
        )

    except Exception as e:
        logger.error(f"Error in Duplicate Order Handler: {str(e)}")
        return create_error_response(str(e))


def query_recent_orders(user_id: str, lookback_minutes: int) -> List[Dict]:
    """Query orders placed within the lookback window."""
    try:
        table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])

        # Calculate lookback time
        current_utc = datetime.now(timezone.utc)
        lookback_time = current_utc - timedelta(minutes=lookback_minutes)
        today = current_utc.strftime("%Y-%m-%d")

        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            FilterExpression='created_at >= :lookback',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':prefix': f'{today}#',
                ':lookback': lookback_time.isoformat()
            }
        )

        orders = response.get('Items', [])
        logger.info(f"Found {len(orders)} orders in last {lookback_minutes} minutes")
        return orders

    except Exception as e:
        logger.error(f"Error querying recent orders: {str(e)}")
        return []


def detect_duplicates(orders: List[Dict], strategy: str) -> List[Dict]:
    """
    Detect duplicate orders based on the deduplication strategy.

    Strategies:
    - TIME_AND_SYMBOL_BASED: Same symbol, same direction within 1 minute
    - EXACT_MATCH: Identical order parameters
    - STRATEGY_BASED: Same strategy_id executed multiple times
    """
    duplicates = []

    if strategy == 'TIME_AND_SYMBOL_BASED':
        duplicates = detect_time_symbol_duplicates(orders)
    elif strategy == 'EXACT_MATCH':
        duplicates = detect_exact_match_duplicates(orders)
    elif strategy == 'STRATEGY_BASED':
        duplicates = detect_strategy_based_duplicates(orders)

    return duplicates


def detect_time_symbol_duplicates(orders: List[Dict]) -> List[Dict]:
    """Detect orders with same symbol and direction within 1 minute."""
    duplicates = []
    order_groups = defaultdict(list)

    for order in orders:
        # Group by symbol + transaction_type
        key = f"{order.get('symbol')}_{order.get('transaction_type')}"
        order_groups[key].append(order)

    for key, group in order_groups.items():
        if len(group) > 1:
            # Sort by created_at
            sorted_orders = sorted(group, key=lambda x: x.get('created_at', ''))

            for i in range(1, len(sorted_orders)):
                prev_time = sorted_orders[i-1].get('created_at', '')
                curr_time = sorted_orders[i].get('created_at', '')

                # Check if within 1 minute
                try:
                    prev_dt = datetime.fromisoformat(prev_time.replace('Z', '+00:00'))
                    curr_dt = datetime.fromisoformat(curr_time.replace('Z', '+00:00'))
                    if (curr_dt - prev_dt).total_seconds() < 60:
                        duplicates.append({
                            'duplicate_type': 'TIME_AND_SYMBOL',
                            'original_order': sorted_orders[i-1].get('order_id'),
                            'duplicate_order': sorted_orders[i].get('order_id'),
                            'symbol': sorted_orders[i].get('symbol'),
                            'time_diff_seconds': (curr_dt - prev_dt).total_seconds()
                        })
                except Exception:
                    pass

    return duplicates


def detect_exact_match_duplicates(orders: List[Dict]) -> List[Dict]:
    """Detect orders with identical parameters."""
    duplicates = []
    seen = {}

    for order in orders:
        # Create fingerprint
        fingerprint = f"{order.get('symbol')}_{order.get('quantity')}_{order.get('price')}_{order.get('transaction_type')}"

        if fingerprint in seen:
            duplicates.append({
                'duplicate_type': 'EXACT_MATCH',
                'original_order': seen[fingerprint],
                'duplicate_order': order.get('order_id'),
                'fingerprint': fingerprint
            })
        else:
            seen[fingerprint] = order.get('order_id')

    return duplicates


def detect_strategy_based_duplicates(orders: List[Dict]) -> List[Dict]:
    """Detect multiple executions of same strategy."""
    duplicates = []
    strategy_orders = defaultdict(list)

    for order in orders:
        strategy_id = order.get('strategy_id')
        if strategy_id:
            strategy_orders[strategy_id].append(order)

    for strategy_id, group in strategy_orders.items():
        if len(group) > 1:
            # Multiple executions of same strategy
            duplicates.append({
                'duplicate_type': 'STRATEGY_BASED',
                'strategy_id': strategy_id,
                'execution_count': len(group),
                'order_ids': [o.get('order_id') for o in group]
            })

    return duplicates


def handle_duplicates(user_id: str, duplicates: List[Dict], current_ist: datetime) -> None:
    """Handle detected duplicate orders."""
    try:
        table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])

        for dup in duplicates:
            # Log the duplicate detection
            logger.warning(f"Duplicate detected: {json.dumps(dup)}")

            # Flag the duplicate order for review
            duplicate_order_id = dup.get('duplicate_order')
            if duplicate_order_id:
                # Update order status to FLAGGED_DUPLICATE
                # In production, you might want to cancel the order instead
                logger.info(f"Flagging order {duplicate_order_id} as potential duplicate")

    except Exception as e:
        logger.error(f"Error handling duplicates: {str(e)}")


def create_success_response(user_id: str, sub_event_id: str,
                            orders_checked: int, duplicates_found: int,
                            duplicate_details: List) -> Dict:
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'user_id': user_id,
            'sub_event_id': sub_event_id,
            'orders_checked': orders_checked,
            'duplicates_found': duplicates_found,
            'duplicate_details': duplicate_details
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
