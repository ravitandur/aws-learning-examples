"""
Marketplace Manager Lambda Handler

Handles marketplace template browsing and admin management:
- GET /marketplace/templates - Browse marketplace templates
- POST /admin/marketplace/enable/{basket_id} - Enable marketplace for basket
- PUT /admin/marketplace/disable/{basket_id} - Disable marketplace for basket
- GET /partner/marketplace/templates - Browse templates via Partner API
"""

import json
import os
import sys
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
REGION = os.environ.get('REGION', 'ap-south-1')


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for marketplace management operations.
    """
    log_lambda_event(logger, event, context)

    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}

        # Route based on method and path
        if http_method == 'GET' and '/templates' in path:
            return handle_browse_templates(event)
        elif http_method == 'POST' and '/enable/' in path:
            basket_id = path_parameters.get('basket_id')
            return handle_enable_marketplace(event, basket_id)
        elif http_method == 'PUT' and '/disable/' in path:
            basket_id = path_parameters.get('basket_id')
            return handle_disable_marketplace(event, basket_id)
        else:
            return create_error_response(
                status_code=400,
                error_code="INVALID_REQUEST",
                message=f"Unsupported operation: {http_method} {path}"
            )

    except Exception as e:
        logger.error(f"Error in marketplace manager: {str(e)}")
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message=str(e)
        )


def handle_browse_templates(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Browse marketplace templates.

    Query params:
    - category: Filter by category (INCOME, GROWTH, HEDGING, etc.)
    - sort_by: Sort field (subscribers, performance, created_at)
    - limit: Number of results (default 20)
    """
    query_params = event.get('queryStringParameters') or {}
    category = query_params.get('category')
    sort_by = query_params.get('sort_by', 'subscribers')
    limit = int(query_params.get('limit', 20))

    logger.info(f"Browsing marketplace templates: category={category}, sort_by={sort_by}, limit={limit}")

    # TODO: Implement DynamoDB query using MarketplaceDiscovery GSI
    # For now, return empty list
    templates = []

    return create_success_response(
        data={
            "templates": templates,
            "count": len(templates),
            "category": category,
            "sort_by": sort_by
        },
        message="Marketplace templates retrieved successfully"
    )


def handle_enable_marketplace(event: Dict[str, Any], basket_id: str) -> Dict[str, Any]:
    """
    Enable marketplace listing for a basket (admin only).

    Request body:
    - category: Marketplace category (INCOME, GROWTH, HEDGING, SPECULATIVE)
    - pricing: Pricing configuration
    - description: Public description
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

    category = body.get('category', 'GENERAL')
    pricing = body.get('pricing', {})
    description = body.get('description', '')

    logger.info(f"Enabling marketplace for basket {basket_id}: category={category}")

    # TODO: Implement DynamoDB update to enable marketplace
    # - Update basket record with marketplace_enabled=True
    # - Set marketplace_category for GSI3
    # - Store pricing and description

    return create_success_response(
        data={
            "basket_id": basket_id,
            "marketplace_enabled": True,
            "category": category
        },
        message=f"Marketplace enabled for basket {basket_id}"
    )


def handle_disable_marketplace(event: Dict[str, Any], basket_id: str) -> Dict[str, Any]:
    """
    Disable marketplace listing for a basket (admin only).
    """
    if not basket_id:
        return create_error_response(
            status_code=400,
            error_code="MISSING_BASKET_ID",
            message="basket_id is required"
        )

    logger.info(f"Disabling marketplace for basket {basket_id}")

    # TODO: Implement DynamoDB update to disable marketplace
    # - Update basket record with marketplace_enabled=False
    # - Remove marketplace_category

    return create_success_response(
        data={
            "basket_id": basket_id,
            "marketplace_enabled": False
        },
        message=f"Marketplace disabled for basket {basket_id}"
    )
