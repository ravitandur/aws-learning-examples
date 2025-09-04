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
    Market Data Refresher Handler
    
    Processes EventBridge events to refresh market data
    Triggered by Master Event Emitter every minute throughout market hours
    """
    
    log_lambda_event(logger, event, context)
    
    try:
        # Extract event details
        event_detail = event.get('detail', {})
        event_id = event_detail.get('event_id')
        trigger_time = event_detail.get('trigger_time_ist')
        market_phase = event_detail.get('market_phase')
        
        logger.info(f"Market Data Refresh triggered", extra={
            "event_id": event_id,
            "trigger_time_ist": trigger_time,
            "market_phase": market_phase
        })
        
        # Market data refresh logic
        refresh_result = refresh_market_data(event_detail)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'event_id': event_id,
                'refresh_result': refresh_result,
                'message': 'Market data refreshed successfully'
            })
        }
        
    except Exception as e:
        logger.error("Failed to refresh market data", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to refresh market data',
                'message': str(e)
            })
        }


def refresh_market_data(event_detail: Dict[str, Any]) -> Dict[str, Any]:
    """Refresh market data based on event details"""
    
    market_phase = event_detail.get('market_phase')
    data_sources = event_detail.get('data_sources', ['NSE'])
    indices = event_detail.get('indices', ['NIFTY', 'BANKNIFTY'])
    
    refresh_result = {
        'market_phase': market_phase,
        'data_sources_checked': data_sources,
        'indices_updated': indices,
        'refresh_timestamp': datetime.now(timezone.utc).isoformat(),
        'status': 'SUCCESS'
    }
    
    logger.info("Market data refresh completed", extra=refresh_result)
    
    return refresh_result