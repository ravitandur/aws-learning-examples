import json
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Union
import os
import sys
from decimal import Decimal


# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


# Add paths for imports
sys.path.append("/opt/python")
sys.path.append("/var/task")  # Add current directory to path
sys.path.append("/var/task/option_baskets")  # Add option_baskets directory to path

# Import shared logger directly (with fixed LogRecord handling)
from shared_utils.logger import (
    setup_logger,
    log_lambda_event,
    log_user_action,
    log_api_response,
)

logger = setup_logger(__name__)


# ✅ REMOVED: populate_broker_allocation_for_strategy function - no longer needed with clean separation


def generate_schedule_key(
    weekday: str, execution_time: str, execution_type: str, strategy_id: str
) -> str:
    """
    🕒 Generate hierarchical schedule key for GSI4 (UserScheduleDiscovery)

    Format: "SCHEDULE#{WEEKDAY}#{TIME}#{TYPE}#{STRATEGY_ID}"

    Examples:
    - Entry: "SCHEDULE#MON#09:30#ENTRY#strategy-iron-condor-001"
    - Exit: "SCHEDULE#MON#15:20#EXIT#strategy-iron-condor-001"

    Query Examples:
    - All Monday strategies: begins_with("SCHEDULE#MON")
    - Monday 9:30 strategies: begins_with("SCHEDULE#MON#09:30")
    - Monday 9:30 entries: begins_with("SCHEDULE#MON#09:30#ENTRY")
    - Specific strategy: begins_with("SCHEDULE#MON#09:30#ENTRY#strategy-001")

    Benefits:
    - Hierarchical database-level filtering
    - Self-documenting key structure
    - Precise query targeting
    - Easy to understand and maintain
    """
    return f"SCHEDULE#{weekday.upper()}#{execution_time}#{execution_type.upper()}#{strategy_id}"


def delete_strategy_schedules(user_id: str, strategy_id: str, table) -> dict:
    """
    🧹 Delete all schedule entries for a specific strategy to prevent orphaned records

    This function is critical for data integrity - when strategies are deleted,
    their associated schedule entries must also be removed to prevent:
    - EventBridge execution errors on non-existent strategies
    - Database bloat from orphaned schedule records
    - Performance degradation in GSI2 schedule queries

    Args:
        user_id: User ID owning the strategy
        strategy_id: Strategy ID whose schedules need cleanup
        table: DynamoDB table resource

    Returns:
        Dictionary with cleanup results: {
            'deleted_count': int,
            'failed_count': int,
            'errors': list
        }
    """
    try:
        logger.info(
            "Starting schedule cleanup for strategy",
            extra={
                "user_id": user_id,
                "strategy_id": strategy_id,
                "operation": "delete_strategy_schedules"
            }
        )

        # Query for all schedule entries belonging to this strategy
        # Pattern: All items with sort_key starting with "SCHEDULE#" that belong to this strategy
        response = table.query(
            KeyConditionExpression="user_id = :user_id AND begins_with(sort_key, :schedule_prefix)",
            ExpressionAttributeValues={
                ":user_id": user_id,
                ":schedule_prefix": "SCHEDULE#",
                ":strategy_id": strategy_id,
            },
            # Filter for schedules belonging to this specific strategy
            FilterExpression="strategy_id = :strategy_id",
        )

        schedules_to_delete = response.get('Items', [])
        deleted_count = 0
        failed_count = 0
        errors = []

        logger.info(
            f"Found {len(schedules_to_delete)} schedule entries to delete for strategy {strategy_id}"
        )

        # Use batch writer for efficient deletion
        with table.batch_writer() as batch:
            for schedule in schedules_to_delete:
                try:
                    batch.delete_item(
                        Key={
                            'user_id': schedule['user_id'],
                            'sort_key': schedule['sort_key']
                        }
                    )
                    deleted_count += 1
                    logger.debug(
                        f"Deleted schedule entry: {schedule['sort_key']} for strategy {strategy_id}"
                    )
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to delete schedule {schedule.get('sort_key', 'unknown')}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)

        logger.info(
            "Schedule cleanup completed",
            extra={
                "user_id": user_id,
                "strategy_id": strategy_id,
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "operation": "delete_strategy_schedules"
            }
        )

        return {
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'errors': errors
        }

    except Exception as e:
        logger.error(
            "Failed to cleanup strategy schedules",
            extra={
                "error": str(e),
                "user_id": user_id,
                "strategy_id": strategy_id,
                "operation": "delete_strategy_schedules"
            }
        )
        return {
            'deleted_count': 0,
            'failed_count': 0,
            'errors': [f"Schedule cleanup failed: {str(e)}"]
        }


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Phase 1 Lambda function to manage strategies using hybrid architecture
    Handles CRUD operations for strategies and legs using single table design
    """

    # Log the incoming Lambda event (sanitized)
    log_lambda_event(logger, event, context)

    try:
        # Get user ID from Cognito authorizer context
        user_id = None
        if "requestContext" in event and "authorizer" in event["requestContext"]:
            claims = event["requestContext"]["authorizer"].get("claims", {})
            user_id = claims.get("sub") or claims.get("cognito:username")

        if not user_id:
            return {
                "statusCode": 401,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {
                        "error": "Unauthorized",
                        "message": "User ID not found in request context",
                    }
                ),
            }

        # Get HTTP method and path parameters
        http_method = event["httpMethod"]
        path_parameters = event.get("pathParameters") or {}
        basket_id = path_parameters.get("basket_id")
        strategy_id = path_parameters.get("strategy_id")

        logger.info(
            "Processing strategy request",
            extra={
                "user_id": user_id,
                "http_method": http_method,
                "basket_id": basket_id,
                "strategy_id": strategy_id,
            },
        )

        # Initialize AWS clients for hybrid architecture
        dynamodb = boto3.resource("dynamodb", region_name=os.environ["REGION"])
        trading_configurations_table = dynamodb.Table(
            os.environ["TRADING_CONFIGURATIONS_TABLE"]
        )

        # Check for bulk delete special endpoint
        resource_path = event.get("resource", "")
        if http_method == "DELETE" and basket_id and "bulk-delete" in resource_path:
            return handle_bulk_delete_strategies(
                event, user_id, basket_id, trading_configurations_table
            )

        # Route based on HTTP method and parameters
        if http_method == "POST" and basket_id:
            return handle_create_strategy(
                event, user_id, basket_id, trading_configurations_table
            )
        elif http_method == "GET" and basket_id and not strategy_id:
            return handle_list_strategies(
                event, user_id, basket_id, trading_configurations_table
            )
        elif http_method == "GET" and not basket_id and not strategy_id:
            return handle_get_available_strategies(
                event, user_id, trading_configurations_table
            )
        elif http_method == "GET" and strategy_id:
            return handle_get_strategy(
                event, user_id, strategy_id, trading_configurations_table
            )
        elif http_method == "PUT" and strategy_id:
            return handle_update_strategy(
                event, user_id, strategy_id, trading_configurations_table
            )
        elif http_method == "DELETE" and strategy_id:
            return handle_delete_strategy(
                event, user_id, strategy_id, trading_configurations_table
            )
        else:
            return {
                "statusCode": 405,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": "Method not allowed"}),
            }

    except Exception as e:
        logger.error("Unexpected error in strategy handler", extra={"error": str(e)})
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": "Internal server error", "message": str(e)}),
        }


def handle_create_strategy(event, user_id, basket_id, table):
    """Create a new strategy with legs using single table design"""

    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})

        # Extract strategy data from user request
        strategy_name = body.get("name", "").strip()
        description = body.get("description", "").strip()
        underlying = body.get("underlying", "").upper()  # NIFTY, BANKNIFTY, etc.
        expiry_type = body.get("expiry_type", "weekly").lower()  # weekly or monthly
        product = body.get("product", "").upper()  # NRML or MIS
        entry_time = body.get("entry_time", "09:30")  # "09:30" format
        exit_time = body.get("exit_time", "15:20")  # "15:20" format
        entry_days = body.get(
            "entry_days", ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
        )
        exit_days = body.get(
            "exit_days", ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
        )
        legs = body.get("legs", [])  # List of leg configurations

        # Extract missing fields (Phase 2: Add missing field storage)
        move_sl_to_cost = body.get("move_sl_to_cost", False)
        range_breakout = body.get("range_breakout", False)
        range_breakout_time = body.get("range_breakout_time")  # Format: "HH:MM" e.g. "09:45"
        trading_type = body.get("trading_type", "").upper()
        intraday_exit_mode = body.get("intraday_exit_mode", "SAME_DAY").upper()

        # Extract strategy-level risk management fields (Phase 3: Target Profit & Stop Loss)
        target_profit = body.get("target_profit")  # {enabled: bool, type: str, value: number}
        mtm_stop_loss = body.get("mtm_stop_loss")  # {enabled: bool, type: str, value: number}

        # Extract POSITIONAL trading fields (Phase 4: Complete field support)
        entry_trading_days_before_expiry = body.get("entry_trading_days_before_expiry")
        exit_trading_days_before_expiry = body.get("exit_trading_days_before_expiry")

        # Validate required fields
        if not strategy_name or not underlying or not product or not legs:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {
                        "error": "Missing required fields",
                        "message": "strategy_name, underlying, product, and legs are required",
                    }
                ),
            }

        # ✅ NEW: Validate legs and enhance with lot configuration
        enhanced_legs, leg_validation_error = validate_and_enhance_legs(legs)
        if leg_validation_error:
            return leg_validation_error

        # Validate product field (user requirement)
        if product not in ["NRML", "MIS"]:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {
                        "error": "Invalid product",
                        "message": "Product must be NRML (positional) or MIS (intraday)",
                    }
                ),
            }

        # Validate underlying (user requirement)
        valid_underlyings = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
        if underlying not in valid_underlyings:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {
                        "error": "Invalid underlying",
                        "message": f'Underlying must be one of: {", ".join(valid_underlyings)}',
                    }
                ),
            }

        # Check if basket exists
        basket_response = table.get_item(
            Key={"user_id": user_id, "sort_key": f"BASKET#{basket_id}"}
        )

        if "Item" not in basket_response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": "Basket not found"}),
            }

        # Generate strategy ID and current timestamp
        strategy_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()

        # Phase 1: Single table structure for strategy
        strategy_item = {
            # Single table structure
            "user_id": user_id,  # Partition key
            "sort_key": f"STRATEGY#{strategy_id}",  # Sort key
            # Basic Information
            "strategy_id": strategy_id,
            "basket_id": basket_id,
            "strategy_name": strategy_name,
            "description": description,
            # Trading Configuration (User-specified requirements)
            "underlying": underlying,  # NIFTY, BANKNIFTY, etc.
            "expiry_type": expiry_type,  # weekly, monthly
            "product": product,  # NRML (positional) or MIS (intraday)
            # Phase 1: Removed derived fields (leg_count, is_intra_day) - calculated on-demand
            # Phase 2: Add missing fields from payload
            "move_sl_to_cost": move_sl_to_cost,
            "range_breakout": range_breakout,
            "range_breakout_time": range_breakout_time,
            "trading_type": trading_type,
            "intraday_exit_mode": intraday_exit_mode,
            # Timing Configuration
            "entry_time": entry_time,
            "exit_time": exit_time,
            "entry_days": entry_days,
            "exit_days": exit_days,
            # Leg Information
            "legs": enhanced_legs,  # Store enhanced legs with lots configuration
            # Performance Metrics (initialized)
            "total_return": Decimal("0"),
            "success_rate": Decimal("0"),
            "execution_count": 0,
            "last_execution_date": None,
            # Status & Metadata
            "status": "ACTIVE",
            "created_at": current_time,
            "updated_at": current_time,
            "version": 1,
            # Single table entity type identifier
            "entity_type": "STRATEGY",
            # GSI attributes for strategy-specific queries
            "entity_type_priority": f"STRATEGY#{strategy_name}",  # For GSI1 sorting
            # GSI attributes for execution schedule (CRITICAL FOR PERFORMANCE)
            # NOTE: Main strategy record no longer has execution_schedule_key
            # Weekday-specific schedule entries are created separately below
            # Strategy-level risk management (Phase 3: TP/SL Storage)
            "target_profit": target_profit,
            "mtm_stop_loss": mtm_stop_loss,
            # POSITIONAL trading fields (Phase 4: Complete field support)
            "entry_trading_days_before_expiry": entry_trading_days_before_expiry,
            "exit_trading_days_before_expiry": exit_trading_days_before_expiry,
        }

        # Store main strategy in single table
        table.put_item(Item=strategy_item)

        # ✅ REMOVED: No longer populating broker allocation in schedule entries (clean separation)

        # 🚀 REVOLUTIONARY: Create weekday-specific execution schedule entries
        # This prevents weekend/holiday executions and enables precise weekday filtering
        weekday_abbr_map = {
            "MONDAY": "MON",
            "TUESDAY": "TUE",
            "WEDNESDAY": "WED",
            "THURSDAY": "THU",
            "FRIDAY": "FRI",
            "SATURDAY": "SAT",
            "SUNDAY": "SUN",
        }

        # Create ENTRY schedule entries for each specified weekday
        for weekday in entry_days:
            weekday_abbr = weekday_abbr_map.get(weekday, weekday[:3].upper())

            entry_schedule_item = {
                "user_id": user_id,
                "sort_key": generate_schedule_key(
                    weekday_abbr, entry_time, "ENTRY", strategy_id
                ),
                # 🎯 LIGHTWEIGHT: Only essential scheduling data (70-80% size reduction)
                "strategy_id": strategy_id,
                "basket_id": basket_id,
                "execution_time": entry_time,
                "weekday": weekday,  # Single weekday for this schedule entry
                "execution_type": "ENTRY",
                "status": "ACTIVE",
                "entity_type": "SCHEDULE",
                "created_at": current_time,
                "updated_at": current_time,
                # 🚀 GSI: User-Centric Schedule Discovery key for simplified architecture
                "schedule_key": generate_schedule_key(
                    weekday_abbr, entry_time, "ENTRY", strategy_id
                ),
                # ❌ REMOVED HEAVY DATA (loaded just-in-time at execution):
                # - strategy_name, underlying, product (available via strategy query)
                # - legs (available via strategy query)
                # - execution_schedule_key, execution_time_slot, user_strategy_composite (unused legacy)
            }

            table.put_item(Item=entry_schedule_item)
            logger.debug(
                f"✅ Created ENTRY schedule: ENTRY#{weekday_abbr}#{entry_time}#{strategy_id}"
            )

        # Create EXIT schedule entries for each specified weekday
        for weekday in exit_days:
            weekday_abbr = weekday_abbr_map.get(weekday, weekday[:3].upper())

            exit_schedule_item = {
                "user_id": user_id,
                "sort_key": generate_schedule_key(
                    weekday_abbr, exit_time, "EXIT", strategy_id
                ),
                # 🎯 LIGHTWEIGHT: Only essential scheduling data (70-80% size reduction)
                "strategy_id": strategy_id,
                "basket_id": basket_id,
                "execution_time": exit_time,
                "weekday": weekday,  # Single weekday for this schedule entry
                "execution_type": "EXIT",
                "status": "ACTIVE",
                "entity_type": "SCHEDULE",
                "created_at": current_time,
                "updated_at": current_time,
                # 🚀 GSI: User-Centric Schedule Discovery key for simplified architecture
                "schedule_key": generate_schedule_key(
                    weekday_abbr, exit_time, "EXIT", strategy_id
                ),
                # ❌ REMOVED HEAVY DATA (loaded just-in-time at execution):
                # - strategy_name, underlying, product (available via strategy query)
                # - legs (available via strategy query)
                # - execution_schedule_key, execution_time_slot, user_strategy_composite (unused legacy)
            }

            table.put_item(Item=exit_schedule_item)
            logger.debug(
                f"✅ Created EXIT schedule: EXIT#{weekday_abbr}#{exit_time}#{strategy_id}"
            )

        total_schedules = len(entry_days) + len(exit_days)
        logger.info(
            f"🎯 Created strategy with {len(entry_days)} entry + {len(exit_days)} exit weekday schedules = {total_schedules} total"
        )

        log_user_action(
            logger,
            user_id,
            "strategy_created",
            {
                "strategy_id": strategy_id,
                "basket_id": basket_id,
                "strategy_name": strategy_name,
                "underlying": underlying,
                "leg_count": len(enhanced_legs),
            },
        )

        # Return response without sensitive data
        response_item = {k: v for k, v in strategy_item.items()}

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "success": True,
                    "data": response_item,
                    "message": "Strategy created successfully",
                },
                cls=DecimalEncoder,
            ),
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": "Invalid JSON in request body"}),
        }
    except Exception as e:
        logger.error(
            "Failed to create strategy", extra={"error": str(e), "user_id": user_id}
        )
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": "Failed to create strategy", "message": str(e)}
            ),
        }


def handle_list_strategies(event, user_id, basket_id, table):
    """Get all strategies for a basket using single table query"""

    try:
        # First verify basket exists and user owns it
        basket_response = table.get_item(
            Key={"user_id": user_id, "sort_key": f"BASKET#{basket_id}"}
        )

        if "Item" not in basket_response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": "Basket not found"}),
            }

        # Query all strategies for the user using sort key pattern
        response = table.query(
            KeyConditionExpression="user_id = :user_id AND begins_with(sort_key, :strategy_prefix)",
            ExpressionAttributeValues={
                ":user_id": user_id,
                ":strategy_prefix": "STRATEGY#",
                ":basket_id": basket_id,
            },
            # Filter by basket_id
            FilterExpression="basket_id = :basket_id",
        )

        strategies = response["Items"]

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "success": True,
                    "data": strategies,
                    "count": len(strategies),
                    "basket_id": basket_id,
                    "message": f"Retrieved {len(strategies)} strategies",
                },
                cls=DecimalEncoder,
            ),
        }

    except Exception as e:
        logger.error(
            "Failed to retrieve strategies", extra={"error": str(e), "user_id": user_id}
        )
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": "Failed to retrieve strategies", "message": str(e)}
            ),
        }


def handle_get_strategy(event, user_id, strategy_id, table):
    """Get specific strategy details using single table structure"""

    try:
        response = table.get_item(
            Key={"user_id": user_id, "sort_key": f"STRATEGY#{strategy_id}"}
        )

        if "Item" not in response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": "Strategy not found"}),
            }

        strategy = response["Item"]

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "success": True,
                    "data": strategy,
                    "message": "Strategy retrieved successfully",
                },
                cls=DecimalEncoder,
            ),
        }

    except Exception as e:
        logger.error(
            "Failed to retrieve strategy", extra={"error": str(e), "user_id": user_id}
        )
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": "Failed to retrieve strategy", "message": str(e)}
            ),
        }


def handle_update_strategy(event, user_id, strategy_id, table):
    """Update an existing strategy using single table structure"""

    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})

        # Check if strategy exists
        response = table.get_item(
            Key={"user_id": user_id, "sort_key": f"STRATEGY#{strategy_id}"}
        )

        if "Item" not in response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": "Strategy not found"}),
            }

        # Update allowed fields
        current_time = datetime.now(timezone.utc).isoformat()
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}

        # Only allow updates to specific fields
        # Phase 4: Added missing fields to updatable fields
        updatable_fields = [
            "strategy_name",
            "description",
            "entry_time",
            "exit_time",
            "entry_days",
            "exit_days",
            "legs",
            "status",
            # Phase 4: Add missing fields from payload
            "move_sl_to_cost",
            "range_breakout",
            "range_breakout_time",
            "trading_type",
            "intraday_exit_mode",
            "product",  # Allow product type updates (MIS/NRML)
            "underlying",  # Allow underlying updates (NIFTY/BANKNIFTY/etc)
            "expiry_type",  # Allow expiry type updates (weekly/monthly)
            "entry_trading_days_before_expiry",  # POSITIONAL trading entry days
            "exit_trading_days_before_expiry",   # POSITIONAL trading exit days
            "target_profit",     # Strategy-level target profit {type, value}
            "mtm_stop_loss",     # Strategy-level stop loss {type, value}
        ]

        for field in updatable_fields:
            if field in body:
                # Handle reserved keywords with ExpressionAttributeNames
                if field == "status":
                    field_name = "#status_field"
                    expression_attribute_names["#status_field"] = "status"
                else:
                    field_name = field

                update_expression_parts.append(f"{field_name} = :{field}")
                expression_attribute_values[f":{field}"] = body[field]

                # Phase 1: Removed leg_count update logic (derived field calculated on-demand)

        # Always update the updated_at timestamp and increment version
        update_expression_parts.extend(
            ["updated_at = :updated_at", "version = version + :one"]
        )
        expression_attribute_values[":updated_at"] = current_time
        expression_attribute_values[":one"] = 1

        if update_expression_parts:
            update_params = {
                "Key": {"user_id": user_id, "sort_key": f"STRATEGY#{strategy_id}"},
                "UpdateExpression": "SET " + ", ".join(update_expression_parts),
                "ExpressionAttributeValues": expression_attribute_values,
            }

            # Only add ExpressionAttributeNames if we have reserved keywords
            if expression_attribute_names:
                update_params["ExpressionAttributeNames"] = expression_attribute_names

            table.update_item(**update_params)

        log_user_action(
            logger, user_id, "strategy_updated", {"strategy_id": strategy_id}
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "success": True,
                    "message": "Strategy updated successfully",
                    "strategy_id": strategy_id,
                }
            ),
        }

    except Exception as e:
        logger.error(
            "Failed to update strategy", extra={"error": str(e), "user_id": user_id}
        )
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": "Failed to update strategy", "message": str(e)}
            ),
        }


def handle_delete_strategy(event, user_id, strategy_id, table):
    """Delete a strategy using single table structure"""

    try:
        # Check if strategy exists and user owns it
        response = table.get_item(
            Key={"user_id": user_id, "sort_key": f"STRATEGY#{strategy_id}"}
        )

        if "Item" not in response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": "Strategy not found"}),
            }

        strategy = response["Item"]
        basket_id = strategy.get("basket_id")

        # Check if strategy has active positions (future enhancement)
        # For now, allow deletion

        # 🧹 CRITICAL: Delete associated schedule entries BEFORE deleting strategy
        # This prevents orphaned schedule records that cause execution errors
        schedule_cleanup_result = delete_strategy_schedules(user_id, strategy_id, table)

        logger.info(
            "Schedule cleanup completed for strategy deletion",
            extra={
                "user_id": user_id,
                "strategy_id": strategy_id,
                "schedules_deleted": schedule_cleanup_result['deleted_count'],
                "schedules_failed": schedule_cleanup_result['failed_count'],
                "operation": "single_strategy_deletion"
            }
        )

        # Delete the strategy
        table.delete_item(
            Key={"user_id": user_id, "sort_key": f"STRATEGY#{strategy_id}"}
        )

        log_user_action(
            logger, user_id, "strategy_deleted", {"strategy_id": strategy_id}
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "success": True,
                    "message": "Strategy deleted successfully",
                    "strategy_id": strategy_id,
                }
            ),
        }

    except Exception as e:
        logger.error(
            "Failed to delete strategy", extra={"error": str(e), "user_id": user_id}
        )
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": "Failed to delete strategy", "message": str(e)}
            ),
        }


def handle_bulk_delete_strategies(event, user_id, basket_id, table):
    """
    🗑️ Bulk delete all strategies in a basket with transaction safety

    This function safely deletes all strategies belonging to a user in a specific basket.
    Uses batch operations for efficiency while maintaining data integrity.

    Args:
        event: Lambda event object
        user_id: ID of the user performing the operation
        basket_id: ID of the basket containing strategies to delete
        table: DynamoDB table resource

    Returns:
        HTTP response with deletion results and counts
    """

    try:
        # First, get all strategies for this basket to validate ownership
        logger.info(
            "Starting bulk delete operation",
            extra={
                "user_id": user_id,
                "basket_id": basket_id,
                "operation": "bulk_delete_strategies"
            }
        )

        # Query all strategies for this user using the same working pattern from handle_list_strategies
        response = table.query(
            KeyConditionExpression="user_id = :user_id AND begins_with(sort_key, :strategy_prefix)",
            ExpressionAttributeValues={
                ":user_id": user_id,
                ":strategy_prefix": "STRATEGY#",
                ":basket_id": basket_id,
            },
            FilterExpression="basket_id = :basket_id",
        )

        strategies_to_delete = response.get('Items', [])
        strategy_count = len(strategies_to_delete)

        if strategy_count == 0:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({
                    "error": "No strategies found",
                    "message": f"No strategies found in basket {basket_id} for bulk deletion",
                    "deleted_count": 0,
                    "failed_count": 0
                }),
            }

        # 🧹 CRITICAL: Delete all schedule entries for these strategies FIRST
        # This prevents orphaned schedule records that cause execution errors
        schedule_cleanup_totals = {'deleted_count': 0, 'failed_count': 0, 'errors': []}

        logger.info(
            f"Starting schedule cleanup for {strategy_count} strategies in bulk deletion"
        )

        # Clean up schedules for each strategy before deleting strategies
        for strategy in strategies_to_delete:
            strategy_id = strategy['sort_key'].replace('STRATEGY#', '')
            schedule_result = delete_strategy_schedules(user_id, strategy_id, table)

            # Aggregate results
            schedule_cleanup_totals['deleted_count'] += schedule_result['deleted_count']
            schedule_cleanup_totals['failed_count'] += schedule_result['failed_count']
            schedule_cleanup_totals['errors'].extend(schedule_result['errors'])

        logger.info(
            "Schedule cleanup completed for bulk strategy deletion",
            extra={
                "user_id": user_id,
                "basket_id": basket_id,
                "total_schedules_deleted": schedule_cleanup_totals['deleted_count'],
                "total_schedules_failed": schedule_cleanup_totals['failed_count'],
                "operation": "bulk_strategy_deletion_schedule_cleanup"
            }
        )

        # Batch delete strategies for efficiency
        deleted_count = 0
        failed_count = 0
        failed_strategy_ids = []

        # Process in batches of 25 (DynamoDB batch limit)
        batch_size = 25
        for i in range(0, len(strategies_to_delete), batch_size):
            batch = strategies_to_delete[i:i + batch_size]

            # Prepare batch delete request
            with table.batch_writer() as batch_writer:
                for strategy in batch:
                    try:
                        strategy_id = strategy['sort_key'].replace('STRATEGY#', '')

                        # Delete the strategy
                        batch_writer.delete_item(
                            Key={
                                'user_id': user_id,
                                'sort_key': strategy['sort_key']
                            }
                        )

                        deleted_count += 1

                        # Log individual deletion
                        logger.info(
                            "Strategy deleted in bulk operation",
                            extra={
                                "user_id": user_id,
                                "strategy_id": strategy_id,
                                "basket_id": basket_id
                            }
                        )

                    except Exception as strategy_error:
                        failed_count += 1
                        strategy_id = strategy.get('sort_key', 'unknown').replace('STRATEGY#', '')
                        failed_strategy_ids.append(strategy_id)
                        logger.error(
                            "Failed to delete strategy in bulk operation",
                            extra={
                                "user_id": user_id,
                                "strategy_id": strategy_id,
                                "error": str(strategy_error)
                            }
                        )

        # Log the bulk operation completion
        log_user_action(
            logger, user_id, "bulk_strategies_deleted",
            {
                "basket_id": basket_id,
                "total_strategies": strategy_count,
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "failed_strategy_ids": failed_strategy_ids
            }
        )

        # Prepare response based on results
        if failed_count == 0:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({
                    "success": True,
                    "message": f"Successfully deleted {deleted_count} strategies from basket {basket_id}",
                    "deleted_count": deleted_count,
                    "failed_count": failed_count,
                    "basket_id": basket_id
                }),
            }
        else:
            return {
                "statusCode": 207,  # Multi-Status for partial success
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({
                    "success": True,
                    "message": f"Bulk deletion completed with {failed_count} failures. {deleted_count} strategies deleted successfully.",
                    "deleted_count": deleted_count,
                    "failed_count": failed_count,
                    "failed_strategy_ids": failed_strategy_ids,
                    "basket_id": basket_id
                }),
            }

    except Exception as e:
        logger.error(
            "Failed to perform bulk delete operation",
            extra={
                "error": str(e),
                "user_id": user_id,
                "basket_id": basket_id
            }
        )
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "error": "Failed to bulk delete strategies",
                "message": str(e),
                "deleted_count": 0,
                "failed_count": 0
            }),
        }


def validate_and_enhance_legs(legs: List[Dict]) -> Union[tuple[List[Dict], None], tuple[None, Dict]]:
    """
    ✅ NEW: Validate legs and enhance with lot configuration support

    This function validates each leg and ensures proper lot configuration.
    Users can now specify 'lots' per leg during strategy creation.

    Args:
        legs: List of leg configurations from user input

    Returns:
        tuple: (enhanced_legs, validation_error)
        - enhanced_legs: List of legs with lots configuration
        - validation_error: Dict with error response if validation fails, None if valid
    """

    if not legs or len(legs) == 0:
        return None, {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "error": "Invalid legs configuration",
                    "message": "At least one leg is required for strategy",
                }
            ),
        }

    # Validate maximum legs per strategy (business rule)
    if len(legs) > 6:
        return None, {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "error": "Too many legs",
                    "message": "Maximum 6 legs allowed per strategy",
                }
            ),
        }

    enhanced_legs = []

    for i, leg in enumerate(legs):
        try:
            # Required fields for each leg (UPDATED: Removed underlying, expiry_type - now strategy-level only)
            required_fields = [
                "option_type",
                "action",
                "lots",
                "selection_method",
            ]
            for field in required_fields:
                if field not in leg or leg[field] is None:
                    return None, {
                        "statusCode": 400,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*",
                        },
                        "body": json.dumps(
                            {
                                "error": f"Missing required field in leg {i+1}",
                                "message": f'Field "{field}" is required for leg {i+1}',
                            }
                        ),
                    }

            # Validate option_type
            if leg["option_type"].upper() not in ["CE", "PE"]:
                return None, {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    "body": json.dumps(
                        {
                            "error": f"Invalid option_type in leg {i+1}",
                            "message": "option_type must be CE or PE",
                        }
                    ),
                }

            # Validate action
            if leg["action"].upper() not in ["BUY", "SELL"]:
                return None, {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    "body": json.dumps(
                        {
                            "error": f"Invalid action in leg {i+1}",
                            "message": "action must be BUY or SELL",
                        }
                    ),
                }



            # Validate selection criteria
            selection_method = leg.get("selection_method", "ATM_POINTS")
            valid_selection_methods = [
                "ATM_POINTS",
                "ATM_PERCENT",
                "PREMIUM",
                "PERCENTAGE_OF_STRADDLE_PREMIUM",
            ]
            if selection_method not in valid_selection_methods:
                return None, {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    "body": json.dumps(
                        {
                            "error": f"Invalid selection_method in leg {i+1}",
                            "message": f"selection_method must be one of {valid_selection_methods}",
                        }
                    ),
                }

            # Validate selection_value based on method
            selection_value = leg.get("selection_value")
            if selection_value is None:
                return None, {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    "body": json.dumps(
                        {
                            "error": f"Missing selection_value in leg {i+1}",
                            "message": f"selection_value is required for {selection_method}",
                        }
                    ),
                }

            if not isinstance(selection_value, (int, float)):
                return None, {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    "body": json.dumps(
                        {
                            "error": f"Invalid selection_value in leg {i+1}",
                            "message": "selection_value must be numeric",
                        }
                    ),
                }

            # Validate selection_operator based on method
            selection_operator = leg.get("selection_operator")
            if selection_method in ["PREMIUM", "PERCENTAGE_OF_STRADDLE_PREMIUM"]:
                if not selection_operator:
                    return None, {
                        "statusCode": 400,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*",
                        },
                        "body": json.dumps(
                            {
                                "error": f"Missing selection_operator in leg {i+1}",
                                "message": f"{selection_method} method requires selection_operator",
                            }
                        ),
                    }
                elif selection_operator not in ["CLOSEST", "GTE", "LTE"]:
                    return None, {
                        "statusCode": 400,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*",
                        },
                        "body": json.dumps(
                            {
                                "error": f"Invalid selection_operator in leg {i+1}",
                                "message": "selection_operator must be CLOSEST, GTE, or LTE",
                            }
                        ),
                    }
            elif selection_method in ["ATM_POINTS", "ATM_PERCENT"]:
                # ATM methods should not have operator
                if selection_operator is not None:
                    return None, {
                        "statusCode": 400,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*",
                        },
                        "body": json.dumps(
                            {
                                "error": f"Invalid selection_operator in leg {i+1}",
                                "message": f"{selection_method} method should not have selection_operator",
                            }
                        ),
                    }

            # Validate lots configuration (lots is now a required field)
            lots = leg.get("lots")
            try:
                lots = int(lots)
                if lots <= 0:
                    raise ValueError("Lots must be positive")
                if lots > 1000:  # Business rule: maximum lots per leg
                    raise ValueError("Lots cannot exceed 1000")
            except (ValueError, TypeError):
                return None, {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    "body": json.dumps(
                        {
                            "error": f"Invalid lots in leg {i+1}",
                            "message": "lots must be a positive integer between 1 and 1000",
                        }
                    ),
                }

            # Create enhanced leg with validated data - PRESERVE ALL INCOMING ATTRIBUTES
            # Start with all original leg attributes to prevent data loss
            enhanced_leg = dict(leg)  # Preserve ALL incoming fields including stop_loss, target_profit, etc.

            # Add/override with required enhancements and validated data
            enhanced_leg.update({
                # Generate unique leg ID
                "leg_id": str(uuid.uuid4()),
                "leg_index": i + 1,
                # Core leg configuration (normalized)
                "option_type": leg["option_type"].upper(),
                "action": leg["action"].upper(),
                "lots": lots,
                # Dynamic strike selection criteria (NO static strike)
                "selection_method": selection_method,
                "selection_value": selection_value,
                "selection_operator": selection_operator,
                # Metadata
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

            enhanced_legs.append(enhanced_leg)

        except Exception as e:
            return None, {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {"error": f"Error processing leg {i+1}", "message": str(e)}
                ),
            }

    logger.info(f"✅ Enhanced {len(enhanced_legs)} legs with lots configuration")

    # Log lots configuration for debugging
    lots_summary = [
        f"Leg {leg['leg_index']}: {leg['lots']} lots" for leg in enhanced_legs
    ]
    logger.debug(f"📊 Lots configuration: {', '.join(lots_summary)}")

    return enhanced_legs, None  # No validation error


def handle_get_available_strategies(event, user_id, table):
    """Get all available strategies for user (across all baskets) - for basketService.getAvailableStrategies()"""

    try:
        # Query all strategies for the user using sort key pattern
        response = table.query(
            KeyConditionExpression="user_id = :user_id AND begins_with(sort_key, :strategy_prefix)",
            ExpressionAttributeValues={
                ":user_id": user_id,
                ":strategy_prefix": "STRATEGY#",
            },
        )

        strategies = response["Items"]

        # Transform strategies to match the expected interface for the frontend
        available_strategies = []
        for strategy in strategies:
            available_strategy = {
                "strategyId": strategy.get("strategy_id"),
                "strategyName": strategy.get("strategy_name"),
                "strategyType": strategy.get(
                    "underlying", "UNKNOWN"
                ),  # Use underlying as strategy type
                "status": strategy.get("status", "UNKNOWN"),
                "legs": strategy.get("leg_count", 0),
            }
            available_strategies.append(available_strategy)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "success": True,
                    "data": available_strategies,
                    "count": len(available_strategies),
                    "message": f"Retrieved {len(available_strategies)} available strategies",
                },
                cls=DecimalEncoder,
            ),
        }

    except Exception as e:
        logger.error(
            "Failed to retrieve available strategies",
            extra={"error": str(e), "user_id": user_id},
        )
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": "Failed to retrieve available strategies", "message": str(e)}
            ),
        }
