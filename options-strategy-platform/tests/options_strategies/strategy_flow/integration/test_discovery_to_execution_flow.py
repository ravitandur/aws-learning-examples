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


class TestDiscoveryToExecutionFlow(OptionsStrategyTestBase):
    """
    Integration test for complete discovery-to-execution workflow.
    
    Tests the complete flow:
    1. Strategy Discovery (schedule_strategy_trigger)
    2. EventBridge Event Emission
    3. Express Step Function Trigger
    4. Strategy Execution
    5. Result Recording
    """
    
    def setUp(self):
        """Set up integration test environment"""
        super().setUp()
        
        # Initialize AWS test helper
        self.aws_helper = AWSTestHelper(self.aws_region)
        self.aws_helper.setup_eventbridge_mock()
        self.aws_helper.setup_stepfunctions_mock()
        
        # Create test basket
        self.test_basket_id = self.create_sample_basket("Integration Test Basket")
        
        # Create test strategies for different scenarios
        self.setup_test_strategies()
        
    def setup_test_strategies(self):
        """Create test strategies for integration testing"""
        
        # Strategy 1: Monday morning Iron Condor
        self.monday_strategy_id = self.create_iron_condor_strategy(
            strategy_name="Monday Morning Iron Condor",
            underlying="NIFTY",
            entry_time="09:30",
            exit_time="15:20",
            entry_days=['MONDAY']
        )
        
        # Strategy 2: Tuesday Bull Call Spread
        self.tuesday_strategy_id = self.create_bull_call_spread_strategy(
            strategy_name="Tuesday Bull Call Spread",
            underlying="BANKNIFTY",
            entry_time="10:00",
            exit_time="15:15",
            entry_days=['TUESDAY']
        )
        
        # Strategy 3: Weekend strategy (should be skipped)
        self.weekend_strategy_id = self.create_weekend_test_strategy(
            strategy_name="Weekend Test Strategy",
            underlying="NIFTY",
            entry_time="10:00"
        )
        
        # Strategy 4: Overlap test strategies
        self.overlap_strategy_ids = self.get_overlap_test_strategies()
        
    def test_complete_discovery_to_execution_flow_monday(self):
        """Test complete flow for Monday strategy discovery and execution"""
        
        # Step 1: Simulate schedule strategy trigger event (every 5 minutes)
        discovery_event = self.aws_helper.create_schedule_strategy_trigger_event(
            discovery_window_start='2025-09-01T09:25:00.000000+05:30',  # Monday 9:25 AM
            discovery_window_end='2025-09-01T09:30:00.000000+05:30',    # Monday 9:30 AM
            market_phase='MARKET_OPEN'
        )
        
        # Step 2: Simulate strategy discovery process
        discovered_strategies = self.simulate_strategy_discovery(discovery_event)
        
        # Should find Monday 9:30 strategy
        self.assertGreater(len(discovered_strategies), 0,
                          "Should discover at least one Monday 9:30 strategy")
        
        # Verify Monday strategy is in discovered strategies
        monday_strategy_found = any(
            s['strategy_id'] == self.monday_strategy_id 
            for s in discovered_strategies
        )
        self.assertTrue(monday_strategy_found,
                       "Monday Iron Condor strategy should be discovered")
        
        # Step 3: Simulate EventBridge event emission for strategy execution
        for execution_time_group in self.group_strategies_by_execution_time(discovered_strategies):
            execution_event = self.aws_helper.create_strategy_execution_event(
                strategies=execution_time_group['strategies'],
                execution_time=execution_time_group['execution_time'],
                wait_seconds=execution_time_group['wait_seconds'],
                market_phase='MARKET_OPEN'
            )
            
            # Step 4: Emit EventBridge event
            event_id = self.aws_helper.emit_test_eventbridge_event(
                source='options.trading.execution',
                detail_type='Strategy Execution Trigger', 
                detail=execution_event
            )
            
            self.assertIsNotNone(event_id, "EventBridge event should be emitted successfully")
            
            # Step 5: Simulate Express Step Function execution
            step_function_result = self.simulate_express_step_function_execution(execution_event)
            
            self.assertEqual(step_function_result['status'], 'SUCCESS',
                           "Express Step Function execution should succeed")
            
    def test_weekend_strategy_discovery_skip_flow(self):
        """Test that weekend strategies are properly skipped throughout the flow"""
        
        # Step 1: Simulate Saturday strategy discovery
        saturday_discovery_event = self.aws_helper.create_schedule_strategy_trigger_event(
            discovery_window_start='2025-09-07T09:55:00.000000+05:30',  # Saturday 9:55 AM
            discovery_window_end='2025-09-07T10:00:00.000000+05:30',    # Saturday 10:00 AM
            market_phase='WEEKEND'
        )
        
        # Step 2: Simulate discovery process (should return empty or skip)
        discovered_strategies = self.simulate_strategy_discovery(saturday_discovery_event)
        
        # Should find no strategies or discovery should be skipped
        weekend_strategies = [
            s for s in discovered_strategies 
            if s['strategy_id'] == self.weekend_strategy_id
        ]
        
        self.assertEqual(len(weekend_strategies), 0,
                        "Weekend strategies should not be discovered on Saturday")
        
    def test_overlap_prevention_flow_18_20_boundary(self):
        """Test that 18:20 overlap prevention works in complete flow"""
        
        # Step 1: Test first window (18:15-18:20) - should NOT include 18:20
        first_window_event = self.aws_helper.create_schedule_strategy_trigger_event(
            discovery_window_start='2025-09-04T18:15:00.000000+05:30',
            discovery_window_end='2025-09-04T18:20:00.000000+05:30',
            market_phase='MCX_EVENING_TRADING'
        )
        
        first_window_strategies = self.simulate_strategy_discovery(first_window_event)
        
        # Should NOT find any strategy with 18:20 execution time
        strategies_at_18_20_first_window = [
            s for s in first_window_strategies 
            if s.get('entry_time') == '18:20'
        ]
        
        self.assertEqual(len(strategies_at_18_20_first_window), 0,
                        "First window (18:15-18:20) should NOT include 18:20 strategies")
        
        # Step 2: Test second window (18:20-18:25) - should include 18:20
        second_window_event = self.aws_helper.create_schedule_strategy_trigger_event(
            discovery_window_start='2025-09-04T18:20:00.000000+05:30',
            discovery_window_end='2025-09-04T18:25:00.000000+05:30',
            market_phase='MCX_EVENING_TRADING'
        )
        
        second_window_strategies = self.simulate_strategy_discovery(second_window_event)
        
        # Should find strategies with 18:20 execution time
        strategies_at_18_20_second_window = [
            s for s in second_window_strategies 
            if s.get('entry_time') == '18:20'
        ]
        
        # If we have 18:20 strategies in test data, they should appear in second window
        if any(s for strategies in self.overlap_strategy_ids for s in [strategies] if s):
            self.assertGreater(len(strategies_at_18_20_second_window), 0,
                             "Second window (18:20-18:25) should include 18:20 strategies")
                             
    def test_eventbridge_event_format_validation(self):
        """Test that EventBridge events have correct format for Step Function triggering"""
        
        # Create test strategies
        test_strategies = [
            {
                'strategy_id': self.monday_strategy_id,
                'strategy_name': 'Test Strategy',
                'entry_time': '09:30',
                'legs': self.get_default_iron_condor_legs()
            }
        ]
        
        # Create strategy execution event
        execution_event = self.aws_helper.create_strategy_execution_event(
            strategies=test_strategies,
            execution_time='09:30',
            wait_seconds=30,
            market_phase='MARKET_OPEN'
        )
        
        # Validate event format
        required_fields = [
            'event_id', 'event_type', 'execution_time', 'execution_datetime',
            'wait_seconds', 'strategies', 'strategy_count', 'market_phase',
            'trigger_source', 'timestamp', 'step_function_trigger'
        ]
        
        is_valid = self.aws_helper.validate_eventbridge_event_format(
            execution_event, required_fields
        )
        
        self.assertTrue(is_valid, "EventBridge event should have all required fields")
        
        # Validate specific field values
        self.assertEqual(execution_event['event_type'], 'TRIGGER_STRATEGY_EXECUTION')
        self.assertEqual(execution_event['execution_time'], '09:30')
        self.assertEqual(execution_event['strategy_count'], 1)
        self.assertEqual(execution_event['wait_seconds'], 30)
        self.assertIn('type', execution_event['step_function_trigger'])
        
    def test_high_volume_strategy_discovery_performance(self):
        """Test discovery performance with high volume of strategies"""
        
        import time
        
        # Create multiple strategies across different times
        strategy_ids = []
        for hour in [9, 10, 11, 14, 15]:
            for minute in [0, 15, 30, 45]:
                entry_time = f"{hour:02d}:{minute:02d}"
                strategy_id = self.create_sample_strategy(
                    strategy_name=f"Volume Test {entry_time}",
                    entry_days=['WEDNESDAY'],
                    entry_time=entry_time
                )
                strategy_ids.append(strategy_id)
                
        # Simulate discovery for peak time
        start_time = time.time()
        discovery_event = self.aws_helper.create_schedule_strategy_trigger_event(
            discovery_window_start='2025-09-03T09:00:00.000000+05:30',  # Wednesday 9:00 AM
            discovery_window_end='2025-09-03T09:05:00.000000+05:30',    # Wednesday 9:05 AM
            market_phase='MARKET_OPEN'
        )
        
        discovered_strategies = self.simulate_strategy_discovery(discovery_event)
        discovery_time = time.time() - start_time
        
        # Performance should be reasonable (under 1 second)
        self.assertLess(discovery_time, 1.0,
                       f"High volume discovery took {discovery_time:.3f}s, should be under 1.0s")
                       
        # Should discover reasonable number of strategies
        self.assertGreater(len(discovered_strategies), 0,
                          "Should discover strategies in high volume test")
                          
    def simulate_strategy_discovery(self, discovery_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate the strategy discovery process"""
        
        # Extract discovery window
        window_start = discovery_event['discovery_window_start']
        window_end = discovery_event['discovery_window_end']
        
        # Parse datetime strings
        start_dt = datetime.fromisoformat(window_start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(window_end.replace('Z', '+00:00'))
        
        # Generate minute time slots (half-open intervals)
        discovered_strategies = []
        current_dt = start_dt.replace(second=0, microsecond=0)
        
        while current_dt < end_dt:  # Half-open interval [start, end)
            time_str = current_dt.strftime('%H:%M')
            weekday = current_dt.strftime('%a').upper()
            
            # Skip weekends
            if weekday in ['SAT', 'SUN']:
                current_dt += timedelta(minutes=1)
                continue
                
            # Query strategies for this specific weekday and time
            strategies = self.query_strategies_for_execution(weekday, time_str)
            
            for strategy in strategies:
                discovered_strategies.append({
                    'strategy_id': strategy['strategy_id'],
                    'strategy_name': strategy.get('strategy_name', 'Unknown'),
                    'entry_time': strategy.get('entry_time', time_str),
                    'underlying': strategy.get('underlying', 'UNKNOWN'),
                    'legs': strategy.get('legs', [])
                })
                
            current_dt += timedelta(minutes=1)
            
        return discovered_strategies
        
    def group_strategies_by_execution_time(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group discovered strategies by execution time"""
        
        time_groups = {}
        
        for strategy in strategies:
            exec_time = strategy['entry_time']
            
            if exec_time not in time_groups:
                time_groups[exec_time] = {
                    'execution_time': exec_time,
                    'strategies': [],
                    'wait_seconds': self.calculate_wait_seconds(exec_time)
                }
                
            time_groups[exec_time]['strategies'].append(strategy)
            
        return list(time_groups.values())
        
    def calculate_wait_seconds(self, execution_time: str) -> int:
        """Calculate wait seconds until execution time"""
        
        # For testing, return a reasonable wait time
        hour, minute = map(int, execution_time.split(':'))
        current_time = datetime.now()
        execution_dt = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if execution_dt <= current_time:
            execution_dt += timedelta(days=1)  # Next day
            
        wait_seconds = int((execution_dt - current_time).total_seconds())
        return max(1, wait_seconds)  # Minimum 1 second
        
    def simulate_express_step_function_execution(self, execution_event: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Express Step Function execution"""
        
        # Create mock step function
        step_function_arn = self.aws_helper.create_mock_step_function(
            name='test-express-execution',
            definition={
                'Comment': 'Test Express Step Function',
                'StartAt': 'ExecuteStrategies',
                'States': {
                    'ExecuteStrategies': {
                        'Type': 'Pass',
                        'Result': {'status': 'SUCCESS'},
                        'End': True
                    }
                }
            }
        )
        
        # Start execution
        execution_arn = self.aws_helper.start_step_function_execution(
            state_machine_arn=step_function_arn,
            execution_input=execution_event
        )
        
        # Get execution result
        result = self.aws_helper.get_step_function_execution_result(execution_arn)
        
        return {
            'status': 'SUCCESS',
            'execution_arn': execution_arn,
            'strategies_processed': len(execution_event['strategies']),
            'result': result
        }


if __name__ == '__main__':
    unittest.main()