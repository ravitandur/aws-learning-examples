"""
Test event payloads for 3-minute lookahead functionality testing
"""
from datetime import datetime

# Valid 3-minute lookahead event
VALID_3MIN_EVENT = {
    'detail': {
        'event_id': 'test-3min-event-001',
        'discovery_type': 'USER_SPECIFIC_3MIN_LOOKAHEAD',
        'user_id': 'user_test_001',
        'weekday': 'MON',
        'trigger_time_ist': '2025-09-08T12:00:00',
        'market_phase': 'ACTIVE_TRADING',
        'lookahead_window_minutes': 3
    }
}

# Valid event with different time
VALID_5MIN_EVENT = {
    'detail': {
        'event_id': 'test-5min-event-001',
        'discovery_type': 'USER_SPECIFIC_5MIN_LOOKAHEAD',
        'user_id': 'user_test_002',
        'weekday': 'TUE',
        'trigger_time_ist': '2025-09-08T14:15:00',
        'market_phase': 'MARKET_OPEN',
        'lookahead_window_minutes': 5
    }
}

# Missing required fields
INVALID_EVENT_MISSING_FIELDS = {
    'detail': {
        'event_id': 'test-invalid-001',
        'user_id': 'user_test_001'
        # Missing: discovery_type, weekday, trigger_time_ist, market_phase
    }
}

# Invalid trigger time format
INVALID_EVENT_BAD_TIME = {
    'detail': {
        'event_id': 'test-invalid-002',
        'discovery_type': 'USER_SPECIFIC_3MIN_LOOKAHEAD',
        'user_id': 'user_test_001',
        'weekday': 'MON',
        'trigger_time_ist': 'invalid-time-format',
        'market_phase': 'ACTIVE_TRADING',
        'lookahead_window_minutes': 3
    }
}

# Weekend event (should be handled specially)
WEEKEND_EVENT = {
    'detail': {
        'event_id': 'test-weekend-001',
        'discovery_type': 'USER_SPECIFIC_3MIN_LOOKAHEAD',
        'user_id': 'user_test_001',
        'weekday': 'SAT',
        'trigger_time_ist': '2025-09-08T12:00:00',
        'market_phase': 'CLOSED',
        'lookahead_window_minutes': 3
    }
}

# Empty detail
EMPTY_EVENT = {
    'detail': {}
}

# No detail field
NO_DETAIL_EVENT = {}