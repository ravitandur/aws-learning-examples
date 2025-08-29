import json
import boto3
from datetime import datetime, timedelta, timezone
import os

def lambda_handler(event, context):
    """
    Lambda function that generates an event with future timestamp (2 minutes from now)
    and sends it to EventBridge
    """
    
    # Initialize EventBridge client
    eventbridge = boto3.client('events')
    
    # IST timezone offset (UTC+5:30)
    IST = timezone(timedelta(hours=5, minutes=30))
    
    # Get current time in IST and calculate future time (2 minutes from now)
    current_time_ist = datetime.now(IST)
    future_time_ist = current_time_ist + timedelta(minutes=2)
    
    # Convert to UTC for EventBridge (required for Step Functions Wait state)
    current_time_utc = current_time_ist.astimezone(timezone.utc)
    future_time_utc = future_time_ist.astimezone(timezone.utc)
    
    # Format times for logging and event payload
    current_time_str = current_time_ist.strftime('%Y-%m-%d %H:%M:%S IST')
    future_time_str = future_time_ist.strftime('%Y-%m-%d %H:%M:%S IST')
    future_time_iso = future_time_utc.isoformat().replace('+00:00', 'Z')
    
    print(f"Current time: {current_time_str}")
    print(f"Scheduled event time: {future_time_str}")
    
    # Event payload
    event_detail = {
        'eventId': f"scheduled-event-{int(current_time_ist.timestamp())}",
        'currentTime': current_time_str,
        'scheduledTime': future_time_str,
        'scheduledTimeISO': future_time_iso,
        'message': 'Event generated for future execution'
    }
    
    try:
        # Send event to EventBridge
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': 'custom.event.generator',
                    'DetailType': 'Scheduled Lambda Event',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': 'default'
                }
            ]
        )
        
        print(f"Event sent to EventBridge. Response: {response}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Event generated successfully',
                'currentTime': current_time_str,
                'scheduledTime': future_time_str,
                'eventId': event_detail['eventId'],
                'eventBridgeResponse': response
            })
        }
        
    except Exception as e:
        print(f"Error sending event to EventBridge: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to generate event',
                'message': str(e)
            })
        }