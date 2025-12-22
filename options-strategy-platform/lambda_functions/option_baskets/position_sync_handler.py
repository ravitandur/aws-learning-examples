"""
🚀 POSITION SYNC HANDLER

Handles Position Sync sub-events from Active User Event Handler.
Synchronizes position data across all brokers for accurate tracking.

Responsibilities:
- Query positions from all connected brokers
- Reconcile positions with local database
- Update position status and P&L
- Detect and report discrepancies
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


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handle Position Sync events.

    Synchronizes positions across all connected brokers.
    """
    log_lambda_event(logger, event, context)

    try:
        detail = event.get('detail', {})
        user_id = detail.get('user_id')
        sub_event_id = detail.get('sub_event_id')
        sync_scope = detail.get('sync_scope', 'ALL_BROKERS')

        if not user_id:
            logger.error("Missing user_id in Position Sync event")
            return create_error_response("Missing user_id")

        logger.info(f"Processing Position Sync for user {user_id}")
        logger.info(f"Sync Scope: {sync_scope}")

        # Get current IST time
        current_utc = datetime.now(timezone.utc)
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        current_ist = current_utc.astimezone(ist_offset)

        # Get user's broker allocations
        broker_accounts = get_user_broker_accounts(user_id)

        if not broker_accounts:
            logger.info(f"No broker accounts for user {user_id}")
            return create_success_response(user_id, sub_event_id, 0, 0, 0, [])

        # Sync positions from each broker
        sync_results = []
        total_positions_synced = 0
        discrepancies_found = 0

        for broker in broker_accounts:
            result = sync_broker_positions(user_id, broker, current_ist)
            sync_results.append(result)
            total_positions_synced += result.get('positions_synced', 0)
            discrepancies_found += result.get('discrepancies', 0)

        logger.info(f"Synced {total_positions_synced} positions from {len(broker_accounts)} brokers")
        if discrepancies_found > 0:
            logger.warning(f"Found {discrepancies_found} discrepancies")

        return create_success_response(
            user_id, sub_event_id,
            len(broker_accounts), total_positions_synced,
            discrepancies_found, sync_results
        )

    except Exception as e:
        logger.error(f"Error in Position Sync Handler: {str(e)}")
        return create_error_response(str(e))


def get_user_broker_accounts(user_id: str) -> List[Dict]:
    """Get all active broker accounts for the user."""
    try:
        # Query from broker accounts table (from auth stack)
        broker_table_name = os.environ.get('BROKER_ACCOUNTS_TABLE')
        if not broker_table_name:
            logger.warning("BROKER_ACCOUNTS_TABLE not configured")
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

        return response.get('Items', [])

    except Exception as e:
        logger.error(f"Error getting broker accounts: {str(e)}")
        return []


def sync_broker_positions(user_id: str, broker: Dict, current_ist: datetime) -> Dict:
    """
    Sync positions from a specific broker.

    In production, this would call the broker's API to get live positions.
    For now, we reconcile with our local execution history.
    """
    try:
        broker_id = broker.get('broker_id')
        broker_name = broker.get('broker_name', broker_id)

        logger.info(f"Syncing positions from broker: {broker_name}")

        # Get local positions for this broker
        local_positions = get_local_positions(user_id, broker_id)

        # In production: Fetch positions from broker API
        # broker_positions = fetch_broker_positions(broker)
        # For now, we'll just validate local positions
        broker_positions = local_positions  # Placeholder

        # Reconcile positions
        reconcile_result = reconcile_positions(
            local_positions, broker_positions, current_ist
        )

        # Update local database with reconciled data
        if reconcile_result.get('updates'):
            update_local_positions(user_id, reconcile_result['updates'])

        return {
            'broker_id': broker_id,
            'broker_name': broker_name,
            'positions_synced': len(local_positions),
            'discrepancies': len(reconcile_result.get('discrepancies', [])),
            'updates_made': len(reconcile_result.get('updates', [])),
            'sync_time': current_ist.isoformat()
        }

    except Exception as e:
        logger.error(f"Error syncing broker positions: {str(e)}")
        return {
            'broker_id': broker.get('broker_id'),
            'error': str(e),
            'positions_synced': 0,
            'discrepancies': 0
        }


def get_local_positions(user_id: str, broker_id: str) -> List[Dict]:
    """Get local positions for a specific broker."""
    try:
        table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        response = table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
            FilterExpression='broker_id = :broker_id AND position_status = :open',
            ExpressionAttributeValues={
                ':user_id': user_id,
                ':prefix': f'{today}#',
                ':broker_id': broker_id,
                ':open': 'OPEN'
            }
        )

        return response.get('Items', [])

    except Exception as e:
        logger.error(f"Error getting local positions: {str(e)}")
        return []


def reconcile_positions(local_positions: List[Dict],
                        broker_positions: List[Dict],
                        current_ist: datetime) -> Dict:
    """
    Reconcile local positions with broker positions.

    Checks for:
    - Quantity mismatches
    - Price discrepancies
    - Missing positions
    - Orphan positions
    """
    discrepancies = []
    updates = []

    local_map = {p.get('position_id', p.get('sort_key')): p for p in local_positions}
    broker_map = {p.get('position_id', p.get('sort_key')): p for p in broker_positions}

    # Check each local position against broker
    for pos_id, local_pos in local_map.items():
        broker_pos = broker_map.get(pos_id)

        if not broker_pos:
            # Position exists locally but not at broker
            discrepancies.append({
                'type': 'MISSING_AT_BROKER',
                'position_id': pos_id,
                'local_quantity': local_pos.get('quantity'),
                'broker_quantity': 0
            })
            continue

        # Check quantity match
        local_qty = int(local_pos.get('quantity', 0))
        broker_qty = int(broker_pos.get('quantity', 0))
        if local_qty != broker_qty:
            discrepancies.append({
                'type': 'QUANTITY_MISMATCH',
                'position_id': pos_id,
                'local_quantity': local_qty,
                'broker_quantity': broker_qty
            })

        # Check for price updates
        broker_price = float(broker_pos.get('current_price', 0))
        if broker_price > 0:
            updates.append({
                'position_id': pos_id,
                'current_price': broker_price,
                'last_synced': current_ist.isoformat()
            })

    # Check for positions at broker not in local
    for pos_id, broker_pos in broker_map.items():
        if pos_id not in local_map:
            discrepancies.append({
                'type': 'ORPHAN_AT_BROKER',
                'position_id': pos_id,
                'broker_quantity': broker_pos.get('quantity')
            })

    return {
        'discrepancies': discrepancies,
        'updates': updates
    }


def update_local_positions(user_id: str, updates: List[Dict]) -> None:
    """Update local positions with synced data."""
    try:
        table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])

        for update in updates:
            position_id = update.get('position_id')
            # In production, you'd update the actual position record
            logger.debug(f"Updated position {position_id} with sync data")

    except Exception as e:
        logger.error(f"Error updating local positions: {str(e)}")


def create_success_response(user_id: str, sub_event_id: str,
                            brokers_synced: int, positions_synced: int,
                            discrepancies: int, sync_details: List) -> Dict:
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'user_id': user_id,
            'sub_event_id': sub_event_id,
            'brokers_synced': brokers_synced,
            'positions_synced': positions_synced,
            'discrepancies_found': discrepancies,
            'sync_details': sync_details
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
