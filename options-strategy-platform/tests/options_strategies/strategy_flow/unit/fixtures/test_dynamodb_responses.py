"""
Mock DynamoDB responses for testing GSI4 queries and strategy discovery
"""

from .test_strategy_data import SAMPLE_STRATEGY_12_01, SAMPLE_STRATEGY_12_03

# Successful GSI4 query response with strategies found
SUCCESSFUL_GSI4_RESPONSE_WITH_STRATEGIES = {
    'Items': [
        {
            'strategy_id': SAMPLE_STRATEGY_12_01['strategy_id'],
            'strategy_name': SAMPLE_STRATEGY_12_01['strategy_name'],
            'execution_time': SAMPLE_STRATEGY_12_01['execution_time'],
            'execution_type': SAMPLE_STRATEGY_12_01['execution_type'],
            'weekdays': SAMPLE_STRATEGY_12_01['weekdays'],
            'legs': SAMPLE_STRATEGY_12_01.get('legs', []),
            'underlying': SAMPLE_STRATEGY_12_01['underlying'],
            'strategy_type': SAMPLE_STRATEGY_12_01['strategy_type'],
            'sort_key': SAMPLE_STRATEGY_12_01['sort_key'],
            'schedule_key': SAMPLE_STRATEGY_12_01.get('schedule_key', '')
        },
        {
            'strategy_id': SAMPLE_STRATEGY_12_03['strategy_id'],
            'strategy_name': SAMPLE_STRATEGY_12_03['strategy_name'],
            'execution_time': SAMPLE_STRATEGY_12_03['execution_time'],
            'execution_type': SAMPLE_STRATEGY_12_03['execution_type'],
            'weekdays': SAMPLE_STRATEGY_12_03['weekdays'],
            'legs': SAMPLE_STRATEGY_12_03.get('legs', []),
            'underlying': SAMPLE_STRATEGY_12_03['underlying'],
            'strategy_type': SAMPLE_STRATEGY_12_03['strategy_type'],
            'sort_key': SAMPLE_STRATEGY_12_03['sort_key'],
            'schedule_key': SAMPLE_STRATEGY_12_03.get('schedule_key', '')
        }
    ],
    'Count': 2,
    'ScannedCount': 2
}

# Empty response (no strategies found)
EMPTY_GSI4_RESPONSE = {
    'Items': [],
    'Count': 0,
    'ScannedCount': 0
}

# Single strategy response
SINGLE_STRATEGY_RESPONSE = {
    'Items': [
        {
            'strategy_id': SAMPLE_STRATEGY_12_01['strategy_id'],
            'strategy_name': SAMPLE_STRATEGY_12_01['strategy_name'],
            'execution_time': SAMPLE_STRATEGY_12_01['execution_time'],
            'execution_type': SAMPLE_STRATEGY_12_01['execution_type'],
            'weekdays': SAMPLE_STRATEGY_12_01['weekdays'],
            'legs': SAMPLE_STRATEGY_12_01.get('legs', []),
            'underlying': SAMPLE_STRATEGY_12_01['underlying'],
            'strategy_type': SAMPLE_STRATEGY_12_01['strategy_type'],
            'sort_key': SAMPLE_STRATEGY_12_01['sort_key']
        }
    ],
    'Count': 1,
    'ScannedCount': 1
}

# Response with EXIT strategy (sort_key contains EXIT)
EXIT_STRATEGY_RESPONSE = {
    'Items': [
        {
            'strategy_id': 'strategy-exit-001',
            'strategy_name': 'Test Exit Strategy',
            'execution_time': '15:20',
            'execution_type': 'EXIT',
            'weekdays': ['MON', 'TUE', 'WED', 'THU', 'FRI'],
            'underlying': 'NIFTY',
            'strategy_type': 'iron_condor',
            'sort_key': 'EXIT#strategy-exit-001'  # EXIT type
        }
    ],
    'Count': 1,
    'ScannedCount': 1
}

# Response with minimal strategy data (missing optional fields)
MINIMAL_STRATEGY_RESPONSE = {
    'Items': [
        {
            'strategy_id': 'strategy-minimal-001',
            'strategy_name': 'Minimal Strategy',
            'execution_time': '12:01',
            'execution_type': 'ENTRY',
            'sort_key': 'STRATEGY#strategy-minimal-001'
            # Missing: weekdays, legs, underlying, strategy_type
        }
    ],
    'Count': 1,
    'ScannedCount': 1
}

# DynamoDB error responses
THROTTLING_EXCEPTION = {
    'Error': {
        'Code': 'ProvisionedThroughputExceededException',
        'Message': 'The level of configured provisioned throughput for the table was exceeded.'
    }
}

RESOURCE_NOT_FOUND_EXCEPTION = {
    'Error': {
        'Code': 'ResourceNotFoundException',
        'Message': 'Requested resource not found'
    }
}

VALIDATION_EXCEPTION = {
    'Error': {
        'Code': 'ValidationException',
        'Message': 'One or more parameter values were invalid'
    }
}

# Expected GSI4 query parameters
EXPECTED_GSI4_QUERY_PARAMS = {
    'IndexName': 'UserScheduleDiscovery',
    'KeyConditionExpression': 'user_id = :user_id AND begins_with(schedule_key, :pattern)',
    'ExpressionAttributeValues': {
        ':user_id': 'user_test_001',
        ':pattern': 'SCHEDULE#MON#12:01',
        ':active': 'ACTIVE'
    },
    'ExpressionAttributeNames': {'#status': 'status'},
    'ProjectionExpression': 'strategy_id, strategy_name, execution_time, weekdays, legs, underlying, strategy_type, sort_key, schedule_key',
    'FilterExpression': '#status = :active'
}

# Successful SQS send response
SUCCESSFUL_SQS_RESPONSE = {
    'MessageId': 'abcd1234-5678-90ef-ghij-klmnopqrstuv',
    'MD5OfBody': 'mock-md5-hash',
    'MD5OfMessageAttributes': 'mock-md5-attributes'
}

# SQS error response
SQS_ERROR_RESPONSE = {
    'Error': {
        'Code': 'QueueDoesNotExist',
        'Message': 'The specified queue does not exist.'
    }
}