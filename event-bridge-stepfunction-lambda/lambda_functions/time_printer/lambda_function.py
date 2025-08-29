import json
from datetime import datetime, timedelta, timezone

def lambda_handler(event, context):
    """
    Lambda function that prints the current time when invoked by Step Functions
    """
    # IST timezone offset (UTC+5:30)
    IST = timezone(timedelta(hours=5, minutes=30))

    # Get current time in IST and calculate future time (2 minutes from now)
    current_time_ist = datetime.now(IST)

    # Format times for logging and event payload
    current_time_str = current_time_ist.strftime('%Y-%m-%d %H:%M:%S IST')

    print(f"Lambda Function 2 executed at: {current_time_str} event:{json.dumps(event)}")
    
    # Log the input event from Step Functions
    print(f"Received event: {json.dumps(event, indent=2)}")
    
    # Extract scheduled time from the event if available
    scheduled_time = None
    if 'scheduledTimeISO' in event:
        scheduled_time = event['scheduledTimeISO']
        print(f"This execution was scheduled for: {scheduled_time}")
    
    # Return success response
    return {
        'statusCode': 200,
        'executionTime': current_time_str,
        'message': f'Lambda Function 2 executed successfully at {current_time_str}',
        'inputEvent': event,
        'scheduledTime': scheduled_time
    }