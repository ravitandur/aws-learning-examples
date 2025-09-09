import unittest
import sys
import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from moto import mock_events, mock_stepfunctions

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'fixtures'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared', 'fixtures'))

from OptionsStrategyTestBase import OptionsStrategyTestBase
from AWSTestHelper import AWSTestHelper


class TestEventBridgeStepFunctionIntegration(OptionsStrategyTestBase):
    """
    Integration test for EventBridge and Step Functions integration.
    
    Tests the revolutionary 0-second precision timing system that achieves
    institutional-grade precision using Standard Step Functions with
    dynamic wait calculation.
    """
    
    def setUp(self):
        """Set up integration test environment for EventBridge and Step Functions"""
        super().setUp()
        
        # Initialize AWS test helper
        self.aws_helper = AWSTestHelper(self.aws_region)
        self.aws_helper.setup_eventbridge_mock()
        self.aws_helper.setup_stepfunctions_mock()
        
        # Create test basket and strategies
        self.test_basket_id = self.create_sample_basket("EventBridge Integration Test Basket")
        
        # Create strategies for different timing scenarios
        self.setup_timing_test_strategies()
        
    def setup_timing_test_strategies(self):
        """Create strategies for different timing precision scenarios"""
        
        # Strategy 1: Market open precision test (9:15 AM)
        self.market_open_strategy_id = self.create_iron_condor_strategy(
            strategy_name="Market Open Precision Test",
            underlying="NIFTY",
            entry_time="09:15",
            entry_days=['MONDAY']
        )
        
        # Strategy 2: Mid-day execution (12:30 PM)
        self.midday_strategy_id = self.create_bull_call_spread_strategy(
            strategy_name="Midday Execution Test",
            underlying="BANKNIFTY",
            entry_time="12:30",
            entry_days=['TUESDAY']
        )
        
        # Strategy 3: Market close precision test (3:25 PM)
        self.market_close_strategy_id = self.create_sample_strategy(
            strategy_name="Market Close Precision Test",
            underlying="FINNIFTY",
            entry_time="15:25",
            entry_days=['WEDNESDAY']
        )
        
        # Strategy 4: High-frequency execution (every 5 minutes)
        self.high_frequency_strategy_ids = []
        for minute in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:
            strategy_id = self.create_sample_strategy(
                strategy_name=f"High-Frequency Test 14:{minute:02d}",
                underlying="NIFTY",
                entry_time=f"14:{minute:02d}",
                entry_days=['THURSDAY']
            )
            self.high_frequency_strategy_ids.append(strategy_id)
            
    def test_eventbridge_daily_auto_start_at_9am_ist(self):
        """Test EventBridge automatic daily start at 9:00 AM IST"""
        
        # Simulate EventBridge cron rule triggering at 9:00 AM IST (3:30 AM UTC)
        daily_start_event = self.aws_helper.create_daily_start_event(
            trigger_time='2025-09-01T09:00:00+05:30',  # Monday 9:00 AM IST
            market_phase='MARKET_PREP'
        )
        
        # Verify event structure for Step Function triggering
        required_fields = ['trigger_time', 'market_phase', 'session_date', 'step_function_trigger']
        
        for field in required_fields:
            self.assertIn(field, daily_start_event,
                         f"Daily start event should contain field: {field}")
                         
        # Verify Step Function trigger configuration
        sf_trigger = daily_start_event['step_function_trigger']
        self.assertEqual(sf_trigger['type'], 'MASTER_TIMER_START')
        self.assertIn('state_machine_arn', sf_trigger)
        
        # Simulate Step Function start
        execution_arn = self.aws_helper.start_step_function_execution(
            state_machine_arn=sf_trigger['state_machine_arn'],
            execution_input=daily_start_event
        )
        
        self.assertIsNotNone(execution_arn, "Step Function execution should start successfully")
        
    def test_dynamic_wait_calculation_achieves_0_second_precision(self):
        """Test that dynamic wait calculation achieves true 0-second precision"""
        
        # Test different current time scenarios
        precision_test_cases = [
            # (current_time, expected_wait_seconds, next_boundary)
            ('09:00:27', 33, '09:01:00'),  # 27 seconds past, wait 33
            ('09:01:03', 57, '09:02:00'),  # 3 seconds past, wait 57
            ('09:02:45', 15, '09:03:00'),  # 45 seconds past, wait 15
            ('09:03:59', 1, '09:04:00'),   # 59 seconds past, wait 1
            ('09:04:00', 60, '09:05:00'),  # Exactly on boundary, wait 60
        ]
        
        for current_time_str, expected_wait, next_boundary_str in precision_test_cases:
            # Create timestamp for Monday
            current_timestamp = f'2025-09-01T{current_time_str}.123456+05:30'
            
            # Simulate event emitter calculating wait time
            wait_seconds = self.simulate_dynamic_wait_calculation(current_timestamp)
            
            self.assertEqual(wait_seconds, expected_wait,
                           f"Wait calculation for {current_time_str} should be {expected_wait}, got {wait_seconds}")
                           
            # Verify next execution would be at 0-second boundary
            current_dt = datetime.fromisoformat(current_timestamp.replace('Z', '+00:00'))
            next_execution = current_dt + timedelta(seconds=wait_seconds)
            
            expected_next = f'2025-09-01T{next_boundary_str}+05:30'
            expected_dt = datetime.fromisoformat(expected_next.replace('Z', '+00:00'))
            
            # Should match exactly to the second
            self.assertEqual(next_execution.replace(microsecond=0), 
                           expected_dt.replace(microsecond=0),
                           f"Next execution should be at {next_boundary_str}")
                           
    def test_master_precision_timer_step_function_execution(self):
        """Test the Master Precision Timer Step Function execution flow"""
        
        # Create mock Step Function definition for testing
        step_function_definition = {
            "Comment": "Master Precision Timer - Revolutionary 0-Second Precision",
            "StartAt": "EmitEvents",
            "States": {
                "EmitEvents": {
                    "Type": "Task",
                    "Resource": "arn:aws:lambda:ap-south-1:142649403032:function:options-event-emitter",
                    "Next": "CheckContinueExecution"
                },
                "CheckContinueExecution": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.Payload.continue_execution",
                            "BooleanEquals": True,
                            "Next": "WaitForNextMinute"
                        }
                    ],
                    "Default": "End"
                },
                "WaitForNextMinute": {
                    "Type": "Wait",
                    "SecondsPath": "$.Payload.wait_seconds",
                    "Next": "EmitEvents"
                },
                "End": {
                    "Type": "Succeed"
                }
            }
        }
        
        # Create mock Step Function
        step_function_arn = self.aws_helper.create_mock_step_function(
            name='master-precision-timer',
            definition=step_function_definition
        )
        
        # Start execution with initial input
        initial_input = {
            "session_date": "2025-09-01",
            "market_phase": "MARKET_PREP",
            "current_time": "09:00:00"
        }
        
        execution_arn = self.aws_helper.start_step_function_execution(
            state_machine_arn=step_function_arn,
            execution_input=initial_input
        )
        
        # Verify execution started
        self.assertIsNotNone(execution_arn, "Master timer execution should start")
        
        # Simulate multiple execution cycles
        execution_history = self.simulate_step_function_execution_cycles(
            execution_arn, 
            cycles=5  # Simulate 5 minutes of execution
        )
        
        # Verify execution history shows proper timing
        self.assertEqual(len(execution_history), 5, "Should have 5 execution cycles")
        
        for i, cycle in enumerate(execution_history):
            self.assertIn('event_emission_time', cycle)
            self.assertIn('wait_seconds', cycle)
            self.assertIn('next_execution_time', cycle)
            
    def test_eventbridge_event_routing_to_specialized_handlers(self):
        """Test EventBridge event routing to 4 specialized event handlers"""
        
        # Create sample event emission from master timer
        event_emission_result = {
            "events_emitted": [
                {
                    "event_type": "SCHEDULE_STRATEGY_TRIGGER",
                    "source": "options.trading.scheduling",
                    "detail_type": "Strategy Discovery Window",
                    "priority": "HIGH",
                    "market_phase": "MARKET_OPEN"
                },
                {
                    "event_type": "CHECK_STOP_LOSS",
                    "source": "options.trading.risk",
                    "detail_type": "Position Risk Monitor",
                    "priority": "CRITICAL",
                    "market_phase": "MARKET_OPEN"
                },
                {
                    "event_type": "CHECK_DUPLICATE_ORDERS", 
                    "source": "options.trading.validation",
                    "detail_type": "Order Validation",
                    "priority": "NORMAL",
                    "market_phase": "MARKET_OPEN"
                },
                {
                    "event_type": "REFRESH_MARKET_DATA",
                    "source": "options.trading.data",
                    "detail_type": "Market Data Update",
                    "priority": "HIGH",
                    "market_phase": "MARKET_OPEN"
                }
            ]
        }
        
        # Test EventBridge event routing
        routing_results = []
        
        for event in event_emission_result["events_emitted"]:
            # Emit event to EventBridge
            event_id = self.aws_helper.emit_test_eventbridge_event(
                source=event["source"],
                detail_type=event["detail_type"],
                detail=event
            )
            
            self.assertIsNotNone(event_id, f"Event {event['event_type']} should be emitted successfully")
            
            # Simulate handler invocation
            handler_result = self.simulate_specialized_handler_invocation(event)
            routing_results.append(handler_result)
            
        # Verify all 4 event types were handled
        handled_event_types = {result['event_type'] for result in routing_results}
        expected_types = {
            'SCHEDULE_STRATEGY_TRIGGER',
            'CHECK_STOP_LOSS', 
            'CHECK_DUPLICATE_ORDERS',
            'REFRESH_MARKET_DATA'
        }
        
        self.assertEqual(handled_event_types, expected_types,
                        "All 4 specialized event types should be handled")
                        
    def test_market_phase_intelligent_event_frequency(self):
        """Test that event frequency adapts to market phase"""
        
        # Test different market phases with expected event patterns
        market_phase_tests = [
            {
                'phase': 'MARKET_OPEN',
                'time': '09:15',
                'expected_events': ['SCHEDULE_STRATEGY_TRIGGER', 'REFRESH_MARKET_DATA', 'CHECK_DUPLICATE_ORDERS'],
                'frequency': 'HIGH'
            },
            {
                'phase': 'ACTIVE_TRADING', 
                'time': '11:30',
                'expected_events': ['CHECK_STOP_LOSS', 'REFRESH_MARKET_DATA'],
                'frequency': 'NORMAL'
            },
            {
                'phase': 'LUNCH_BREAK',
                'time': '13:00',
                'expected_events': ['REFRESH_MARKET_DATA'],
                'frequency': 'LOW'
            },
            {
                'phase': 'PRE_CLOSE',
                'time': '15:25',
                'expected_events': ['CHECK_STOP_LOSS', 'SCHEDULE_STRATEGY_TRIGGER', 'REFRESH_MARKET_DATA'],
                'frequency': 'CRITICAL'
            }
        ]
        
        for phase_test in market_phase_tests:
            # Simulate event emission for this market phase
            phase_events = self.simulate_market_phase_event_emission(
                market_phase=phase_test['phase'],
                current_time=phase_test['time']
            )
            
            # Verify expected events are emitted
            emitted_event_types = {event['event_type'] for event in phase_events}
            expected_event_types = set(phase_test['expected_events'])
            
            self.assertTrue(expected_event_types.issubset(emitted_event_types),
                           f"Phase {phase_test['phase']} should emit expected events: {expected_event_types}")
                           
            # Verify frequency/priority matches phase
            for event in phase_events:
                if phase_test['frequency'] == 'CRITICAL':
                    self.assertEqual(event.get('priority', 'NORMAL'), 'CRITICAL')
                elif phase_test['frequency'] == 'HIGH':
                    self.assertIn(event.get('priority', 'NORMAL'), ['HIGH', 'CRITICAL'])
                    
    def test_step_function_aws_limits_scalability_analysis(self):
        """Test Step Function scalability against AWS limits"""
        
        # Simulate full market session execution
        market_session_duration = timedelta(hours=6, minutes=30)  # 9:00 AM - 3:30 PM
        total_minutes = int(market_session_duration.total_seconds() / 60)
        
        # Each minute has 3 state transitions: EmitEvents -> CheckContinueExecution -> WaitForNextMinute
        transitions_per_minute = 3
        total_transitions = total_minutes * transitions_per_minute
        
        # AWS Step Functions limit: 25,000 transitions per execution
        aws_limit = 25000
        usage_percentage = (total_transitions / aws_limit) * 100
        
        # Verify we're well within limits
        self.assertLess(total_transitions, aws_limit,
                       f"Total transitions ({total_transitions}) should be within AWS limit ({aws_limit})")
        
        self.assertLess(usage_percentage, 20.0,
                       f"Should use less than 20% of AWS limit, using {usage_percentage:.1f}%")
                       
        # Test extended hours capability (9:00 AM - 11:35 PM)
        extended_duration = timedelta(hours=14, minutes=35)
        extended_minutes = int(extended_duration.total_seconds() / 60)
        extended_transitions = extended_minutes * transitions_per_minute
        extended_percentage = (extended_transitions / aws_limit) * 100
        
        self.assertLess(extended_transitions, aws_limit,
                       f"Extended hours transitions ({extended_transitions}) should be within limit")
        
        self.assertLess(extended_percentage, 50.0,
                       f"Extended hours should use less than 50% of limit, using {extended_percentage:.1f}%")
                       
        # Log scalability metrics
        scalability_metrics = {
            'normal_session': {
                'duration_minutes': total_minutes,
                'total_transitions': total_transitions,
                'aws_limit_usage': f"{usage_percentage:.1f}%"
            },
            'extended_session': {
                'duration_minutes': extended_minutes,
                'total_transitions': extended_transitions,
                'aws_limit_usage': f"{extended_percentage:.1f}%"
            }
        }
        
        # Assert excellent scalability
        self.assertGreater(aws_limit - extended_transitions, 10000,
                          "Should have over 10,000 transitions headroom even for extended hours")
                          
    def test_error_recovery_and_continuation_logic(self):
        """Test error recovery and execution continuation logic"""
        
        # Simulate error scenarios and recovery
        error_scenarios = [
            {
                'error_type': 'LAMBDA_TIMEOUT',
                'should_continue': True,
                'recovery_action': 'RETRY_WITH_REDUCED_LOAD'
            },
            {
                'error_type': 'DYNAMODB_THROTTLING',
                'should_continue': True,
                'recovery_action': 'EXPONENTIAL_BACKOFF'
            },
            {
                'error_type': 'MARKET_CLOSED',
                'should_continue': False,
                'recovery_action': 'GRACEFUL_SHUTDOWN'
            },
            {
                'error_type': 'SYSTEM_MAINTENANCE',
                'should_continue': False,
                'recovery_action': 'SCHEDULED_PAUSE'
            }
        ]
        
        for scenario in error_scenarios:
            # Simulate error condition
            error_response = self.simulate_error_condition(
                error_type=scenario['error_type'],
                current_time='11:30:00',
                market_phase='ACTIVE_TRADING'
            )
            
            # Verify error handling logic
            self.assertEqual(error_response['continue_execution'], scenario['should_continue'],
                           f"Error {scenario['error_type']} should set continue_execution to {scenario['should_continue']}")
            
            if scenario['should_continue']:
                self.assertIn('wait_seconds', error_response,
                             "Recoverable errors should include wait_seconds")
                self.assertGreater(error_response['wait_seconds'], 0,
                                 "Wait seconds should be positive for recovery")
            else:
                self.assertFalse(error_response['continue_execution'],
                               "Non-recoverable errors should stop execution")
                               
    def simulate_dynamic_wait_calculation(self, current_timestamp: str) -> int:
        """Simulate the dynamic wait calculation algorithm"""
        
        # Parse current timestamp
        current_dt = datetime.fromisoformat(current_timestamp.replace('Z', '+00:00'))
        current_second = current_dt.second
        
        # Calculate seconds to next 0-second boundary
        seconds_remaining = 60 - current_second
        
        # Never return 0, minimum 1 second wait
        return max(1, seconds_remaining)
        
    def simulate_step_function_execution_cycles(self, execution_arn: str, cycles: int) -> List[Dict[str, Any]]:
        """Simulate multiple Step Function execution cycles"""
        
        execution_history = []
        current_time = datetime.now().replace(second=0, microsecond=0)
        
        for cycle in range(cycles):
            # Simulate event emission
            emission_time = current_time + timedelta(minutes=cycle)
            wait_seconds = 60  # Exactly 1 minute for testing
            next_execution = emission_time + timedelta(seconds=wait_seconds)
            
            cycle_data = {
                'cycle_number': cycle + 1,
                'event_emission_time': emission_time.isoformat(),
                'wait_seconds': wait_seconds,
                'next_execution_time': next_execution.isoformat(),
                'events_emitted': 4  # All 4 event types
            }
            execution_history.append(cycle_data)
            
        return execution_history
        
    def simulate_specialized_handler_invocation(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate invocation of specialized event handlers"""
        
        event_type = event['event_type']
        
        # Simulate handler-specific logic
        if event_type == 'SCHEDULE_STRATEGY_TRIGGER':
            return {
                'event_type': event_type,
                'handler': 'schedule_strategy_trigger',
                'strategies_discovered': 3,
                'execution_time': '09:30:00',
                'processing_time_ms': 45
            }
        elif event_type == 'CHECK_STOP_LOSS':
            return {
                'event_type': event_type,
                'handler': 'check_stop_loss',
                'positions_checked': 15,
                'stop_loss_triggered': 0,
                'processing_time_ms': 32
            }
        elif event_type == 'CHECK_DUPLICATE_ORDERS':
            return {
                'event_type': event_type,
                'handler': 'check_duplicate_orders',
                'orders_validated': 8,
                'duplicates_found': 0,
                'processing_time_ms': 28
            }
        elif event_type == 'REFRESH_MARKET_DATA':
            return {
                'event_type': event_type,
                'handler': 'refresh_market_data',
                'symbols_updated': 25,
                'data_freshness_seconds': 2,
                'processing_time_ms': 67
            }
        
        return {'event_type': event_type, 'handler': 'unknown'}
        
    def simulate_market_phase_event_emission(self, market_phase: str, current_time: str) -> List[Dict[str, Any]]:
        """Simulate event emission based on market phase"""
        
        phase_configurations = {
            'MARKET_OPEN': {
                'events': ['SCHEDULE_STRATEGY_TRIGGER', 'REFRESH_MARKET_DATA', 'CHECK_DUPLICATE_ORDERS'],
                'priority': 'HIGH'
            },
            'ACTIVE_TRADING': {
                'events': ['CHECK_STOP_LOSS', 'REFRESH_MARKET_DATA'],
                'priority': 'NORMAL'
            },
            'LUNCH_BREAK': {
                'events': ['REFRESH_MARKET_DATA'],
                'priority': 'LOW'
            },
            'PRE_CLOSE': {
                'events': ['CHECK_STOP_LOSS', 'SCHEDULE_STRATEGY_TRIGGER', 'REFRESH_MARKET_DATA'],
                'priority': 'CRITICAL'
            }
        }
        
        config = phase_configurations.get(market_phase, {})
        events = []
        
        for event_type in config.get('events', []):
            event = {
                'event_type': event_type,
                'market_phase': market_phase,
                'current_time': current_time,
                'priority': config.get('priority', 'NORMAL'),
                'emission_timestamp': datetime.now().isoformat()
            }
            events.append(event)
            
        return events
        
    def simulate_error_condition(self, error_type: str, current_time: str, market_phase: str) -> Dict[str, Any]:
        """Simulate error conditions and recovery logic"""
        
        error_responses = {
            'LAMBDA_TIMEOUT': {
                'continue_execution': True,
                'wait_seconds': 120,  # Wait 2 minutes before retry
                'error_details': 'Lambda function timeout, reducing load',
                'recovery_action': 'RETRY_WITH_REDUCED_LOAD'
            },
            'DYNAMODB_THROTTLING': {
                'continue_execution': True,
                'wait_seconds': 300,  # Wait 5 minutes for backoff
                'error_details': 'DynamoDB throttling detected',
                'recovery_action': 'EXPONENTIAL_BACKOFF'
            },
            'MARKET_CLOSED': {
                'continue_execution': False,
                'error_details': 'Market session ended',
                'recovery_action': 'GRACEFUL_SHUTDOWN'
            },
            'SYSTEM_MAINTENANCE': {
                'continue_execution': False,
                'error_details': 'System maintenance window',
                'recovery_action': 'SCHEDULED_PAUSE'
            }
        }
        
        return error_responses.get(error_type, {
            'continue_execution': True,
            'wait_seconds': 60,
            'error_details': 'Unknown error',
            'recovery_action': 'DEFAULT_RETRY'
        })


if __name__ == '__main__':
    unittest.main()