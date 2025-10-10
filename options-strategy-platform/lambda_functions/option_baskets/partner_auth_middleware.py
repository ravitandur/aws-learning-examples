"""
Partner API Authentication Middleware
Validates partner API keys and enforces rate limiting for B2B2C integrations
"""

import boto3
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
import os
from decimal import Decimal

# Import shared logger
try:
    from shared_utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)


class PartnerAuthMiddleware:
    """
    Middleware for authenticating and rate limiting partner API requests
    """

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'ap-south-1'))
        self.table = self.dynamodb.Table(os.environ.get('TRADING_CONFIGURATIONS_TABLE'))

    def authenticate_partner(self, event: Dict[str, Any]) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Authenticate partner API request

        Args:
            event: Lambda event object

        Returns:
            Tuple of (is_authenticated, partner_context, error_message)
        """

        try:
            # Extract API key and secret from headers
            headers = event.get('headers', {})

            # Handle case-insensitive headers
            headers_lower = {k.lower(): v for k, v in headers.items()}

            # Extract Authorization header (Bearer token format)
            auth_header = headers_lower.get('authorization', '')
            if not auth_header.startswith('Bearer '):
                return False, None, 'Missing or invalid Authorization header'

            api_key = auth_header.replace('Bearer ', '').strip()

            # Extract partner secret from custom header
            api_secret = headers_lower.get('x-partner-secret', '')
            if not api_secret:
                return False, None, 'Missing X-Partner-Secret header'

            # Validate API key format
            if not api_key.startswith('pk_'):
                return False, None, 'Invalid API key format'

            # Extract api_key_id from the key (last part after final underscore before token)
            # Format: pk_{partner_id}_live_{token}
            try:
                parts = api_key.split('_')
                if len(parts) < 4:
                    return False, None, 'Malformed API key'
            except Exception:
                return False, None, 'Invalid API key structure'

            # Fetch partner configuration from DynamoDB
            partner = self._get_partner_by_api_key(api_key)
            if not partner:
                logger.warning("Partner API key not found", extra={"api_key_prefix": api_key[:15]})
                return False, None, 'Invalid API key'

            # Verify partner status
            if partner.get('status') != 'ACTIVE':
                logger.warning("Partner API key not active", extra={
                    "partner_id": partner.get('partner_id'),
                    "status": partner.get('status')
                })
                return False, None, f"API key status: {partner.get('status')}"

            # Verify API secret using bcrypt
            api_secret_hash = partner.get('api_secret_hash', '')
            try:
                secret_matches = bcrypt.checkpw(
                    api_secret.encode('utf-8'),
                    api_secret_hash.encode('utf-8')
                )
            except Exception as e:
                logger.error("Failed to verify API secret", extra={"error": str(e)})
                return False, None, 'Authentication failed'

            if not secret_matches:
                logger.warning("Invalid API secret", extra={"partner_id": partner.get('partner_id')})
                return False, None, 'Invalid API secret'

            # Update last_used_at timestamp (async, don't wait)
            self._update_last_used_timestamp(partner.get('api_key_id'))

            # Return partner context (remove sensitive data)
            partner_context = {
                'api_key_id': partner.get('api_key_id'),
                'partner_id': partner.get('partner_id'),
                'partner_name': partner.get('partner_name'),
                'partner_type': partner.get('partner_type'),
                'broker_id': partner.get('broker_id'),
                'permissions': partner.get('permissions', []),
                'rate_limits': partner.get('rate_limits', {}),
                'revenue_share': partner.get('revenue_share', {}),
                'branding': partner.get('branding', {})
            }

            logger.info("Partner authenticated successfully", extra={
                "partner_id": partner_context['partner_id']
            })

            return True, partner_context, None

        except Exception as e:
            logger.error("Partner authentication error", extra={"error": str(e)})
            return False, None, f"Authentication error: {str(e)}"

    def check_rate_limit(self, partner_context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check if partner has exceeded rate limits

        Args:
            partner_context: Partner context from authentication

        Returns:
            Tuple of (is_within_limits, error_message)
        """

        try:
            api_key_id = partner_context['api_key_id']
            rate_limits = partner_context.get('rate_limits', {})

            # Get current timestamp
            now = datetime.now(timezone.utc)
            current_minute = now.strftime('%Y-%m-%d-%H-%M')
            current_day = now.strftime('%Y-%m-%d')

            # Check minute limit
            minute_limit = rate_limits.get('requests_per_minute', 100)
            minute_count = self._increment_rate_counter(api_key_id, 'minute', current_minute, ttl=60)

            if minute_count > minute_limit:
                logger.warning("Partner exceeded minute rate limit", extra={
                    "partner_id": partner_context['partner_id'],
                    "current_count": minute_count,
                    "limit": minute_limit
                })
                return False, f"Rate limit exceeded: {minute_limit} requests per minute"

            # Check daily limit
            day_limit = rate_limits.get('requests_per_day', 10000)
            day_count = self._increment_rate_counter(api_key_id, 'day', current_day, ttl=86400)

            if day_count > day_limit:
                logger.warning("Partner exceeded daily rate limit", extra={
                    "partner_id": partner_context['partner_id'],
                    "current_count": day_count,
                    "limit": day_limit
                })
                return False, f"Rate limit exceeded: {day_limit} requests per day"

            # Within limits
            return True, None

        except Exception as e:
            logger.error("Rate limit check error", extra={"error": str(e)})
            # Fail open (allow request) to prevent service disruption
            return True, None

    def check_permission(self, partner_context: Dict[str, Any], required_permission: str) -> Tuple[bool, Optional[str]]:
        """
        Check if partner has required permission

        Args:
            partner_context: Partner context from authentication
            required_permission: Permission string (e.g., 'marketplace:subscribe')

        Returns:
            Tuple of (has_permission, error_message)
        """

        permissions = partner_context.get('permissions', [])

        if required_permission in permissions:
            return True, None

        logger.warning("Partner missing required permission", extra={
            "partner_id": partner_context['partner_id'],
            "required_permission": required_permission,
            "available_permissions": permissions
        })

        return False, f"Missing permission: {required_permission}"

    def _get_partner_by_api_key(self, api_key: str) -> Optional[Dict]:
        """Fetch partner configuration by API key"""

        try:
            # Query DynamoDB for partner with matching API key
            response = self.table.query(
                KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :prefix)',
                FilterExpression='api_key = :api_key',
                ExpressionAttributeValues={
                    ':user_id': 'PARTNER',
                    ':prefix': 'PARTNER_API_KEY#',
                    ':api_key': api_key
                }
            )

            items = response.get('Items', [])
            if items:
                return items[0]

            return None

        except Exception as e:
            logger.error("Failed to fetch partner by API key", extra={"error": str(e)})
            return None

    def _increment_rate_counter(self, api_key_id: str, counter_type: str, time_window: str, ttl: int) -> int:
        """
        Increment rate limit counter using DynamoDB

        Args:
            api_key_id: Partner API key ID
            counter_type: 'minute' or 'day'
            time_window: Time window string (e.g., '2025-10-10-14-30' for minute)
            ttl: Time to live in seconds

        Returns:
            Current counter value after increment
        """

        try:
            sort_key = f"RATE_LIMIT#{counter_type.upper()}#{time_window}"

            # Calculate TTL timestamp
            ttl_timestamp = int((datetime.now(timezone.utc) + timedelta(seconds=ttl)).timestamp())

            # Increment counter with atomic operation
            response = self.table.update_item(
                Key={
                    'user_id': f"RATE#{api_key_id}",
                    'sort_key': sort_key
                },
                UpdateExpression='ADD request_count :inc SET ttl = :ttl',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':ttl': ttl_timestamp
                },
                ReturnValues='UPDATED_NEW'
            )

            # Return current count
            return int(response['Attributes'].get('request_count', 1))

        except Exception as e:
            logger.error("Failed to increment rate counter", extra={"error": str(e)})
            # Return 0 to fail open (allow request)
            return 0

    def _update_last_used_timestamp(self, api_key_id: str):
        """Update partner API key last_used_at timestamp (fire and forget)"""

        try:
            self.table.update_item(
                Key={
                    'user_id': 'PARTNER',
                    'sort_key': f'PARTNER_API_KEY#{api_key_id}'
                },
                UpdateExpression='SET last_used_at = :timestamp',
                ExpressionAttributeValues={
                    ':timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            # Log but don't fail the request
            logger.debug("Failed to update last_used_at", extra={"error": str(e)})


def validate_partner_request(event: Dict[str, Any], required_permission: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function for Lambda handlers to validate partner requests

    Args:
        event: Lambda event object
        required_permission: Optional permission to check

    Returns:
        Dict with validation results

    Example usage in Lambda:
        validation = validate_partner_request(event, 'marketplace:subscribe')
        if not validation['authenticated']:
            return {
                'statusCode': 401,
                'body': json.dumps({'error': validation['error']})
            }

        partner = validation['partner_context']
        # Proceed with request logic...
    """

    middleware = PartnerAuthMiddleware()

    # Authenticate partner
    is_authenticated, partner_context, auth_error = middleware.authenticate_partner(event)
    if not is_authenticated:
        return {
            'authenticated': False,
            'error': auth_error,
            'status_code': 401
        }

    # Check rate limits
    within_limits, rate_error = middleware.check_rate_limit(partner_context)
    if not within_limits:
        return {
            'authenticated': True,
            'rate_limited': True,
            'error': rate_error,
            'status_code': 429
        }

    # Check permission if required
    if required_permission:
        has_permission, perm_error = middleware.check_permission(partner_context, required_permission)
        if not has_permission:
            return {
                'authenticated': True,
                'rate_limited': False,
                'authorized': False,
                'error': perm_error,
                'status_code': 403
            }

    # All checks passed
    return {
        'authenticated': True,
        'rate_limited': False,
        'authorized': True,
        'partner_context': partner_context,
        'status_code': 200
    }
