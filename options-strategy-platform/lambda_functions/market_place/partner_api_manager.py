"""
Partner API Manager Lambda Handler

Handles partner API key management and authentication:
- POST /admin/partner-api-keys - Create new partner API key
- GET /admin/partner-api-keys - List partner API keys
- PUT /admin/partner-api-keys/{key_id} - Update partner API key
- DELETE /admin/partner-api-keys/{key_id} - Revoke partner API key
"""

import json
import os
import sys
import uuid
import secrets
import hashlib
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
REGION = os.environ.get('REGION', 'ap-south-1')


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for partner API key management.
    """
    log_lambda_event(logger, event, context)

    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}

        # Route based on method and path
        if http_method == 'POST':
            return handle_create_api_key(event)
        elif http_method == 'GET':
            key_id = path_parameters.get('key_id')
            if key_id:
                return handle_get_api_key(event, key_id)
            else:
                return handle_list_api_keys(event)
        elif http_method == 'PUT':
            key_id = path_parameters.get('key_id')
            return handle_update_api_key(event, key_id)
        elif http_method == 'DELETE':
            key_id = path_parameters.get('key_id')
            return handle_revoke_api_key(event, key_id)
        else:
            return create_error_response(
                status_code=400,
                error_code="INVALID_REQUEST",
                message=f"Unsupported operation: {http_method} {path}"
            )

    except Exception as e:
        logger.error(f"Error in partner API manager: {str(e)}")
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message=str(e)
        )


def generate_api_key() -> tuple:
    """
    Generate a secure API key.

    Returns:
        Tuple of (plain_key, hashed_key)
    """
    # Generate a secure random key
    plain_key = f"qlmp_{secrets.token_urlsafe(32)}"

    # Hash the key for storage
    hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()

    return plain_key, hashed_key


def handle_create_api_key(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new partner API key.

    Request body:
    - partner_name: Name of the partner (required)
    - description: Description of the API key usage
    - permissions: List of allowed operations
    - rate_limit: Requests per minute limit
    """
    # Verify admin authorization
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    groups = claims.get('cognito:groups', '')

    if 'Admins' not in groups:
        return create_error_response(
            status_code=403,
            error_code="FORBIDDEN",
            message="Admin access required"
        )

    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return create_error_response(
            status_code=400,
            error_code="INVALID_JSON",
            message="Invalid JSON in request body"
        )

    partner_name = body.get('partner_name')
    if not partner_name:
        return create_error_response(
            status_code=400,
            error_code="MISSING_PARTNER_NAME",
            message="partner_name is required"
        )

    key_id = str(uuid.uuid4())
    plain_key, hashed_key = generate_api_key()
    now = datetime.now(timezone.utc).isoformat()

    logger.info(f"Creating API key {key_id} for partner: {partner_name}")

    # TODO: Implement DynamoDB operations:
    # 1. Store hashed key (NEVER store plain key)
    # 2. Store partner metadata
    # 3. Set up rate limiting configuration

    api_key_record = {
        "key_id": key_id,
        "partner_name": partner_name,
        "description": body.get('description', ''),
        "permissions": body.get('permissions', ['read']),
        "rate_limit": body.get('rate_limit', 100),
        "status": "active",
        "created_at": now,
        "created_by": claims.get('sub')
    }

    return create_success_response(
        data={
            **api_key_record,
            "api_key": plain_key  # Return plain key ONLY on creation
        },
        message="Partner API key created successfully. Save the API key - it won't be shown again."
    )


def handle_list_api_keys(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    List all partner API keys (admin only).

    Query params:
    - status: Filter by status (active, revoked)
    - limit: Number of results
    """
    # Verify admin authorization
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    groups = claims.get('cognito:groups', '')

    if 'Admins' not in groups:
        return create_error_response(
            status_code=403,
            error_code="FORBIDDEN",
            message="Admin access required"
        )

    query_params = event.get('queryStringParameters') or {}
    status_filter = query_params.get('status')
    limit = int(query_params.get('limit', 50))

    logger.info(f"Listing partner API keys: status={status_filter}, limit={limit}")

    # TODO: Implement DynamoDB query
    api_keys = []

    return create_success_response(
        data={
            "api_keys": api_keys,
            "count": len(api_keys)
        },
        message="Partner API keys retrieved successfully"
    )


def handle_get_api_key(event: Dict[str, Any], key_id: str) -> Dict[str, Any]:
    """
    Get partner API key details (admin only).
    """
    # Verify admin authorization
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    groups = claims.get('cognito:groups', '')

    if 'Admins' not in groups:
        return create_error_response(
            status_code=403,
            error_code="FORBIDDEN",
            message="Admin access required"
        )

    if not key_id:
        return create_error_response(
            status_code=400,
            error_code="MISSING_KEY_ID",
            message="key_id is required"
        )

    logger.info(f"Getting API key details: {key_id}")

    # TODO: Implement DynamoDB get item
    api_key = None

    if not api_key:
        return create_error_response(
            status_code=404,
            error_code="API_KEY_NOT_FOUND",
            message=f"API key {key_id} not found"
        )

    return create_success_response(
        data=api_key,
        message="API key retrieved successfully"
    )


def handle_update_api_key(event: Dict[str, Any], key_id: str) -> Dict[str, Any]:
    """
    Update partner API key settings.
    """
    # Verify admin authorization
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    groups = claims.get('cognito:groups', '')

    if 'Admins' not in groups:
        return create_error_response(
            status_code=403,
            error_code="FORBIDDEN",
            message="Admin access required"
        )

    if not key_id:
        return create_error_response(
            status_code=400,
            error_code="MISSING_KEY_ID",
            message="key_id is required"
        )

    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return create_error_response(
            status_code=400,
            error_code="INVALID_JSON",
            message="Invalid JSON in request body"
        )

    logger.info(f"Updating API key {key_id}: {body}")

    # TODO: Implement DynamoDB update
    # - Update permissions
    # - Update rate limit
    # - Update description

    return create_success_response(
        data={"key_id": key_id, "updated": True},
        message=f"API key {key_id} updated successfully"
    )


def handle_revoke_api_key(event: Dict[str, Any], key_id: str) -> Dict[str, Any]:
    """
    Revoke partner API key (makes it unusable).
    """
    # Verify admin authorization
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    groups = claims.get('cognito:groups', '')

    if 'Admins' not in groups:
        return create_error_response(
            status_code=403,
            error_code="FORBIDDEN",
            message="Admin access required"
        )

    if not key_id:
        return create_error_response(
            status_code=400,
            error_code="MISSING_KEY_ID",
            message="key_id is required"
        )

    logger.info(f"Revoking API key {key_id}")

    # TODO: Implement DynamoDB update to set status=revoked

    return create_success_response(
        data={"key_id": key_id, "status": "revoked"},
        message=f"API key {key_id} revoked successfully"
    )
