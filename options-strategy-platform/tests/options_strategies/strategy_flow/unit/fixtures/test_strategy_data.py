"""
Test strategy data structures for 3-minute lookahead functionality testing
"""

# Sample strategy found by GSI4 query
SAMPLE_STRATEGY_12_01 = {
    'strategy_id': 'strategy-iron-condor-001',
    'strategy_name': 'Test Iron Condor 12:01',
    'execution_time': '12:01',
    'execution_type': 'ENTRY',
    'weekdays': ['MON', 'TUE', 'WED', 'THU', 'FRI'],
    'legs': [
        {
            'leg_type': 'sell_call',
            'strike_offset': 100,
            'quantity': 25
        },
        {
            'leg_type': 'buy_call', 
            'strike_offset': 200,
            'quantity': 25
        }
    ],
    'underlying': 'NIFTY',
    'strategy_type': 'iron_condor',
    'sort_key': 'STRATEGY#strategy-iron-condor-001',
    'schedule_key': 'SCHEDULE#MON#12:01#ENTRY#strategy-iron-condor-001'
}

SAMPLE_STRATEGY_12_03 = {
    'strategy_id': 'strategy-straddle-001',
    'strategy_name': 'Test Straddle 12:03',
    'execution_time': '12:03',
    'execution_type': 'ENTRY',
    'weekdays': ['MON', 'TUE', 'WED', 'THU', 'FRI'],
    'legs': [
        {
            'leg_type': 'buy_call',
            'strike_offset': 0,
            'quantity': 50
        },
        {
            'leg_type': 'buy_put',
            'strike_offset': 0,
            'quantity': 50
        }
    ],
    'underlying': 'BANKNIFTY',
    'strategy_type': 'straddle',
    'sort_key': 'STRATEGY#strategy-straddle-001',
    'schedule_key': 'SCHEDULE#MON#12:03#ENTRY#strategy-straddle-001'
}

# Multiple strategies for testing batch processing
MULTIPLE_STRATEGIES_DIFFERENT_TIMES = [
    SAMPLE_STRATEGY_12_01,
    SAMPLE_STRATEGY_12_03,
    {
        'strategy_id': 'strategy-strangle-001',
        'strategy_name': 'Test Strangle 12:02',
        'execution_time': '12:02',
        'weekdays': ['MON', 'TUE', 'WED', 'THU', 'FRI'],
        'underlying': 'NIFTY',
        'strategy_type': 'strangle',
        'sort_key': 'STRATEGY#strategy-strangle-001'
    }
]

# Strategy with complex broker allocation
STRATEGY_WITH_BROKER_ALLOCATION = {
    'strategy_id': 'strategy-complex-001',
    'strategy_name': 'Complex Multi-Broker Strategy',
    'execution_time': '12:01',
    'weekdays': ['MON', 'TUE', 'WED', 'THU', 'FRI'],
    'broker_allocation': {
        'zerodha': {'lots': 2, 'priority': 1},
        'angel_one': {'lots': 1, 'priority': 2}
    },
    'underlying': 'NIFTY',
    'strategy_type': 'iron_condor',
    'sort_key': 'STRATEGY#strategy-complex-001'
}

# EXIT strategy (vs ENTRY)
EXIT_STRATEGY = {
    'strategy_id': 'strategy-exit-001',
    'strategy_name': 'Test Exit Strategy',
    'execution_time': '15:20',
    'execution_type': 'EXIT',
    'weekdays': ['MON', 'TUE', 'WED', 'THU', 'FRI'],
    'underlying': 'NIFTY',
    'strategy_type': 'iron_condor',
    'sort_key': 'EXIT#strategy-exit-001'  # EXIT instead of STRATEGY
}

# Strategy with missing optional fields
MINIMAL_STRATEGY = {
    'strategy_id': 'strategy-minimal-001',
    'strategy_name': 'Minimal Strategy',
    'execution_time': '12:01',
    'execution_type': 'ENTRY',
    'sort_key': 'STRATEGY#strategy-minimal-001'
    # Missing: weekdays, legs, underlying, strategy_type
}

# Expected SQS message structure for strategy
EXPECTED_SQS_MESSAGE_STRUCTURE = {
    'user_id': 'user_test_001',
    'strategy_id': 'strategy-iron-condor-001',
    'strategy_name': 'Test Iron Condor 12:01',
    'execution_time': '12:01',
    'weekday': 'MON',
    'execution_type': 'ENTRY',
    'strategy_data': {
        # Strategy data embedded
    },
    'market_phase': 'ACTIVE_TRADING',
    'trigger_source': 'user_specific_3min_lookahead_discovery',
    'timestamp': '2025-09-08T12:00:00.000Z',
    'event_id': 'test-3min-event-001',
    'lookahead_window': ['12:01', '12:02', '12:03']
}

# Expected message attributes structure
EXPECTED_MESSAGE_ATTRIBUTES = {
    'UserId': {'StringValue': 'user_test_001', 'DataType': 'String'},
    'StrategyId': {'StringValue': 'strategy-iron-condor-001', 'DataType': 'String'},
    'ExecutionTime': {'StringValue': '12:01', 'DataType': 'String'},
    'Weekday': {'StringValue': 'MON', 'DataType': 'String'},
    'ExecutionType': {'StringValue': 'ENTRY', 'DataType': 'String'},
    'MarketPhase': {'StringValue': 'ACTIVE_TRADING', 'DataType': 'String'},
    'LookaheadWindow': {'StringValue': '12:01,12:02,12:03', 'DataType': 'String'}
}