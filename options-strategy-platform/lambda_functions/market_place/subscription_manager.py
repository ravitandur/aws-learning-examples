"""
Subscription Manager Lambda Handler

Handles user and partner subscription management:
- POST /marketplace/subscribe/{basket_id} - Subscribe to template
- GET /subscriptions - List user's subscriptions
- GET /subscriptions/{subscription_id} - Get subscription details
- PUT /subscriptions/{subscription_id} - Update subscription
- DELETE /subscriptions/{subscription_id} - Cancel subscription
- PUT /subscriptions/{subscription_id}/pause - Pause subscription
- PUT /subscriptions/{subscription_id}/resume - Resume subscription
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from decimal import Decimal

sys.path.append('/opt/python')
sys.path.append('/var/task')

from shared_utils.logger import setup_logger, log_lambda_event
from shared_utils.response_utils import create_success_response, create_error_response

logger = setup_logger(__name__)

# Environment variables
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
TRADING_CONFIGURATIONS_TABLE = os.environ.get('TRADING_CONFIGURATIONS_TABLE')
BROKER_ACCOUNTS_TABLE = os.environ.get('BROKER_ACCOUNTS_TABLE')
REGION = os.environ.get('REGION', 'ap-south-1')


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for subscription management operations.
    """
    log_lambda_event(logger, event, context)

    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}

        # Determine if this is a partner API request
        is_partner = '/partner/' in path

        # Route based on method and path
        if http_method == 'POST' and '/subscribe/' in path:
            basket_id = path_parameters.get('basket_id')
            return handle_subscribe(event, basket_id, is_partner)
        elif http_method == 'GET' and '/subscriptions' in path:
            subscription_id = path_parameters.get('subscription_id')
            if subscription_id:
                return handle_get_subscription(event, subscription_id)
            else:
                return handle_list_subscriptions(event, is_partner)
        elif http_method == 'PUT' and '/pause' in path:
            subscription_id = path_parameters.get('subscription_id')
            return handle_pause_subscription(event, subscription_id)
        elif http_method == 'PUT' and '/resume' in path:
            subscription_id = path_parameters.get('subscription_id')
            return handle_resume_subscription(event, subscription_id)
        elif http_method == 'PUT':
            subscription_id = path_parameters.get('subscription_id')
            return handle_update_subscription(event, subscription_id)
        elif http_method == 'DELETE':
            subscription_id = path_parameters.get('subscription_id')
            return handle_cancel_subscription(event, subscription_id)
        else:
            return create_error_response(
                status_code=400,
                error_code="INVALID_REQUEST",
                message=f"Unsupported operation: {http_method} {path}"
            )

    except Exception as e:
        logger.error(f"Error in subscription manager: {str(e)}")
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message=str(e)
        )


def handle_subscribe(event: Dict[str, Any], basket_id: str, is_partner: bool = False) -> Dict[str, Any]:
    """
    Subscribe to a marketplace template.

    Request body:
    - broker_allocation: Broker allocation configuration
    - auto_trade: Enable/disable auto-trading
    """
    if not basket_id:
        return create_error_response(
            status_code=400,
            error_code="MISSING_BASKET_ID",
            message="basket_id is required"
        )

    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return create_error_response(
            status_code=400,
            error_code="INVALID_JSON",
            message="Invalid JSON in request body"
        )

    # Extract user info from JWT claims or partner API key
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    user_id = claims.get('sub')

    if not user_id and is_partner:
        # For partner API, extract from header or body
        user_id = body.get('user_id')

    if not user_id:
        return create_error_response(
            status_code=401,
            error_code="UNAUTHORIZED",
            message="User identification required"
        )

    subscription_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    logger.info(f"Creating subscription {subscription_id} for user {user_id} to basket {basket_id}")

    # TODO: Implement DynamoDB operations:
    # 1. Verify basket exists and is marketplace-enabled
    # 2. Create subscription record
    # 3. Copy strategies with user's broker allocation
    # 4. Update template subscriber count

    subscription = {
        "subscription_id": subscription_id,
        "user_id": user_id,
        "template_basket_id": basket_id,
        "status": "active",
        "auto_trade": body.get('auto_trade', False),
        "created_at": now,
        "updated_at": now
    }

    return create_success_response(
        data=subscription,
        message=f"Successfully subscribed to basket {basket_id}"
    )


def handle_list_subscriptions(event: Dict[str, Any], is_partner: bool = False) -> Dict[str, Any]:
    """
    List user's subscriptions.

    Query params:
    - status: Filter by status (active, paused, cancelled)
    - limit: Number of results
    """
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    user_id = claims.get('sub')

    if not user_id and is_partner:
        # For partner API, get from query params
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id')

    if not user_id:
        return create_error_response(
            status_code=401,
            error_code="UNAUTHORIZED",
            message="User identification required"
        )

    query_params = event.get('queryStringParameters') or {}
    status_filter = query_params.get('status')
    limit = int(query_params.get('limit', 50))

    logger.info(f"Listing subscriptions for user {user_id}: status={status_filter}, limit={limit}")

    # TODO: Implement DynamoDB query using UserSubscriptions GSI
    subscriptions = []

    return create_success_response(
        data={
            "subscriptions": subscriptions,
            "count": len(subscriptions)
        },
        message="Subscriptions retrieved successfully"
    )


def handle_get_subscription(event: Dict[str, Any], subscription_id: str) -> Dict[str, Any]:
    """
    Get subscription details.
    """
    if not subscription_id:
        return create_error_response(
            status_code=400,
            error_code="MISSING_SUBSCRIPTION_ID",
            message="subscription_id is required"
        )

    logger.info(f"Getting subscription details: {subscription_id}")

    # TODO: Implement DynamoDB get item
    subscription = None

    if not subscription:
        return create_error_response(
            status_code=404,
            error_code="SUBSCRIPTION_NOT_FOUND",
            message=f"Subscription {subscription_id} not found"
        )

    return create_success_response(
        data=subscription,
        message="Subscription retrieved successfully"
    )


def handle_update_subscription(event: Dict[str, Any], subscription_id: str) -> Dict[str, Any]:
    """
    Update subscription settings.
    """
    if not subscription_id:
        return create_error_response(
            status_code=400,
            error_code="MISSING_SUBSCRIPTION_ID",
            message="subscription_id is required"
        )

    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return create_error_response(
            status_code=400,
            error_code="INVALID_JSON",
            message="Invalid JSON in request body"
        )

    logger.info(f"Updating subscription {subscription_id}: {body}")

    # TODO: Implement DynamoDB update
    # - Update broker allocation
    # - Update auto_trade setting
    # - Update other configurable fields

    return create_success_response(
        data={"subscription_id": subscription_id, "updated": True},
        message=f"Subscription {subscription_id} updated successfully"
    )


def handle_pause_subscription(event: Dict[str, Any], subscription_id: str) -> Dict[str, Any]:
    """
    Pause subscription (stops auto-trading but keeps subscription active).
    """
    if not subscription_id:
        return create_error_response(
            status_code=400,
            error_code="MISSING_SUBSCRIPTION_ID",
            message="subscription_id is required"
        )

    logger.info(f"Pausing subscription {subscription_id}")

    # TODO: Implement DynamoDB update to set status=paused

    return create_success_response(
        data={"subscription_id": subscription_id, "status": "paused"},
        message=f"Subscription {subscription_id} paused"
    )


def handle_resume_subscription(event: Dict[str, Any], subscription_id: str) -> Dict[str, Any]:
    """
    Resume a paused subscription.
    """
    if not subscription_id:
        return create_error_response(
            status_code=400,
            error_code="MISSING_SUBSCRIPTION_ID",
            message="subscription_id is required"
        )

    logger.info(f"Resuming subscription {subscription_id}")

    # TODO: Implement DynamoDB update to set status=active

    return create_success_response(
        data={"subscription_id": subscription_id, "status": "active"},
        message=f"Subscription {subscription_id} resumed"
    )


def handle_cancel_subscription(event: Dict[str, Any], subscription_id: str) -> Dict[str, Any]:
    """
    Cancel subscription (permanently).
    """
    if not subscription_id:
        return create_error_response(
            status_code=400,
            error_code="MISSING_SUBSCRIPTION_ID",
            message="subscription_id is required"
        )

    logger.info(f"Cancelling subscription {subscription_id}")

    # TODO: Implement DynamoDB operations:
    # 1. Update subscription status to cancelled
    # 2. Decrement template subscriber count
    # 3. Optionally clean up copied strategies

    return create_success_response(
        data={"subscription_id": subscription_id, "status": "cancelled"},
        message=f"Subscription {subscription_id} cancelled"
    )
