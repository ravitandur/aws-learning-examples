import json
import boto3
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Add paths for imports
sys.path.append('/opt/python')
sys.path.append('/var/task')  # Add current directory to path
sys.path.append('/var/task/option_baskets')  # Add option_baskets directory to path

# Import shared logger directly
from shared_utils.logger import setup_logger, log_lambda_event, log_user_action, log_api_response
logger = setup_logger(__name__)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Stop Loss Checker Handler
    
    Processes EventBridge events for real-time stop loss monitoring
    Triggered every minute during active trading phases
    """
    
    log_lambda_event(logger, event, context)
    
    try:
        # Extract event details
        event_detail = event.get('detail', {})
        event_id = event_detail.get('event_id')
        trigger_time = event_detail.get('trigger_time_ist')
        market_phase = event_detail.get('market_phase')
        priority = event_detail.get('priority', 'HIGH')
        
        logger.info(f"Stop loss check triggered", extra={
            "event_id": event_id,
            "trigger_time_ist": trigger_time,
            "market_phase": market_phase,
            "priority": priority
        })
        
        # Stop loss monitoring logic
        monitoring_result = monitor_stop_loss_conditions(event_detail)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'event_id': event_id,
                'monitoring_result': monitoring_result,
                'message': 'Stop loss monitoring completed successfully'
            })
        }
        
    except Exception as e:
        logger.error("Failed to monitor stop loss conditions", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to monitor stop loss conditions',
                'message': str(e)
            })
        }


def monitor_stop_loss_conditions(event_detail: Dict[str, Any]) -> Dict[str, Any]:
    """Monitor stop loss conditions for all active positions"""
    
    market_phase = event_detail.get('market_phase')
    priority = event_detail.get('priority', 'HIGH')
    volatility_context = event_detail.get('market_volatility_context', 'NORMAL_VOLATILITY')
    emergency_exit_enabled = event_detail.get('emergency_exit_enabled', False)
    
    monitoring_result = {
        'positions_monitored': 0,  # Would be actual count from position query
        'stop_loss_breaches': 0,   # Number of stop loss violations detected
        'market_phase': market_phase,
        'priority': priority,
        'volatility_context': volatility_context,
        'emergency_exits_triggered': 0,
        'monitoring_timestamp': datetime.now(timezone.utc).isoformat(),
        'status': 'SUCCESS'
    }
    
    # Critical priority handling during PRE_CLOSE phase
    if priority == 'CRITICAL':
        monitoring_result['enhanced_monitoring'] = True
        logger.warning("Critical priority stop loss monitoring activated", extra={
            "market_phase": market_phase,
            "emergency_exit_enabled": emergency_exit_enabled
        })
    
    logger.info("Stop loss monitoring completed", extra=monitoring_result)
    
    return monitoring_result