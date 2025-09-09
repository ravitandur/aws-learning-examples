import unittest
import sys
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'fixtures'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared', 'fixtures'))

from OptionsStrategyTestBase import OptionsStrategyTestBase


class TestWeekdaySchedulingLogic(OptionsStrategyTestBase):
    """
    Test weekday-aware scheduling logic for options strategies.
    
    Tests the core functionality that prevents weekend executions and 
    ensures proper weekday filtering in strategy discovery and execution.
    """
    
    def setUp(self):
        """Set up test environment with sample strategies"""
        super().setUp()
        
        # Create sample basket for testing
        self.test_basket_id = self.create_sample_basket("Weekday Test Basket")
        
    def test_strategy_creation_generates_weekday_specific_schedules(self):
        """Test that creating a strategy generates separate weekday schedule entries"""
        
        # Create a strategy with 3 entry days
        entry_days = ['MONDAY', 'WEDNESDAY', 'FRIDAY']
        exit_days = ['TUESDAY', 'THURSDAY']
        
        strategy_id = self.create_iron_condor_strategy(
            strategy_name="Weekday Schedule Test Strategy",
            entry_days=entry_days,
            underlying="NIFTY",
            entry_time="09:30"
        )
        
        # Should create main strategy + 3 entry schedules + 2 exit schedules = 6 total items
        expected_schedules = len(entry_days) + len(exit_days)
        self.assert_strategy_created_successfully(strategy_id, expected_schedules)
        
        # Verify individual schedule entries exist
        for weekday in entry_days:
            weekday_abbr = self.get_weekday_abbr(weekday)
            schedule_key = f'SCHEDULE#{strategy_id}#{weekday_abbr}#ENTRY'
            
            response = self.trading_configurations_table.get_item(
                Key={
                    'user_id': self.test_user_id,
                    'sort_key': schedule_key
                }
            )
            
            self.assertIn('Item', response, f"Entry schedule for {weekday} not found")
            schedule_item = response['Item']
            
            # Verify schedule structure
            self.assertEqual(schedule_item['strategy_id'], strategy_id)
            self.assertEqual(schedule_item['weekday'], weekday)
            self.assertEqual(schedule_item['execution_type'], 'ENTRY')
            
            # Verify weekday-aware execution_schedule_key
            expected_key = f"ENTRY#{weekday_abbr}#09:30#{strategy_id}"
            self.assertEqual(schedule_item['execution_schedule_key'], expected_key)
            
    def test_monday_strategy_discovery_returns_only_monday_strategies(self):
        """Test that Monday strategy discovery only returns Monday strategies"""
        
        # Create strategies for different weekdays
        monday_strategy = self.create_iron_condor_strategy(
            strategy_name="Monday Only Strategy",
            entry_days=['MONDAY'],
            entry_time="09:30"
        )
        
        tuesday_strategy = self.create_bull_call_spread_strategy(
            strategy_name="Tuesday Only Strategy",
            entry_time="09:30"  # Default entry_days includes all weekdays
        )
        
        weekend_strategy = self.create_weekend_test_strategy(
            strategy_name="Weekend Strategy",
            entry_time="09:30"
        )
        
        # Query for Monday 09:30 strategies
        monday_strategies = self.query_strategies_for_execution('MON', '09:30')
        
        # Should find Monday strategy and Tuesday strategy (which has Monday in entry_days)
        # Should NOT find weekend strategy
        self.assertGreaterEqual(len(monday_strategies), 2, 
                               "Should find at least Monday and Tuesday strategies")
        
        # Verify all returned strategies have Monday in their schedule
        for strategy in monday_strategies:
            execution_key = strategy['execution_schedule_key']
            self.assertTrue(execution_key.startswith('ENTRY#MON#09:30#'),
                           f"Strategy {strategy['strategy_id']} has invalid Monday execution key: {execution_key}")
            
    def test_weekend_strategy_discovery_returns_empty_results(self):
        """Test that weekend strategy discovery returns no results"""
        
        # Create strategies for weekdays and weekends
        self.create_iron_condor_strategy(
            strategy_name="Weekday Strategy",
            entry_days=['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'],
            entry_time="10:00"
        )
        
        self.create_weekend_test_strategy(
            strategy_name="Saturday Strategy",
            entry_time="10:00"
        )
        
        # Query for Saturday strategies
        saturday_strategies = self.query_strategies_for_execution('SAT', '10:00')
        self.assertEqual(len(saturday_strategies), 0,
                        "Saturday query should return no strategies")
                        
        # Query for Sunday strategies  
        sunday_strategies = self.query_strategies_for_execution('SUN', '10:00')
        self.assertEqual(len(sunday_strategies), 0,
                        "Sunday query should return no strategies")
                        
    def test_weekday_abbreviation_mapping_works_correctly(self):
        """Test that weekday abbreviation mapping works correctly"""
        
        test_cases = [
            ('MONDAY', 'MON'),
            ('TUESDAY', 'TUE'),
            ('WEDNESDAY', 'WED'),
            ('THURSDAY', 'THU'),
            ('FRIDAY', 'FRI'),
            ('SATURDAY', 'SAT'),
            ('SUNDAY', 'SUN')
        ]
        
        for full_name, expected_abbr in test_cases:
            actual_abbr = self.get_weekday_abbr(full_name)
            self.assertEqual(actual_abbr, expected_abbr,
                           f"Weekday abbreviation for {full_name} should be {expected_abbr}, got {actual_abbr}")
                           
    def test_mixed_weekday_weekend_strategy_creates_correct_schedules(self):
        """Test strategy with mixed weekday/weekend entry days creates only weekday schedules"""
        
        # Create strategy with mixed weekday/weekend entry days
        mixed_days = ['FRIDAY', 'SATURDAY', 'SUNDAY', 'MONDAY']
        
        strategy_id = self.create_sample_strategy(
            strategy_name="Mixed Weekday Weekend Strategy",
            entry_days=mixed_days,
            exit_days=['FRIDAY', 'MONDAY'],  # Only weekdays for exits
            entry_time="14:30"
        )
        
        # Should create schedules for all days (including weekends)
        # The weekend protection happens at query/execution time, not creation time
        expected_schedules = len(mixed_days) + 2  # 4 entry + 2 exit
        self.assert_strategy_created_successfully(strategy_id, expected_schedules)
        
        # Verify weekend schedules exist in database (but won't be found by weekday queries)
        for weekday in ['SATURDAY', 'SUNDAY']:
            weekday_abbr = self.get_weekday_abbr(weekday)
            schedule_key = f'SCHEDULE#{strategy_id}#{weekday_abbr}#ENTRY'
            
            response = self.trading_configurations_table.get_item(
                Key={
                    'user_id': self.test_user_id,
                    'sort_key': schedule_key
                }
            )
            
            self.assertIn('Item', response, f"Weekend schedule for {weekday} should exist in database")
            
    def test_execution_schedule_key_format_is_correct(self):
        """Test that execution_schedule_key follows correct format"""
        
        strategy_id = self.create_iron_condor_strategy(
            strategy_name="Format Test Strategy",
            entry_days=['WEDNESDAY'],
            entry_time="11:45"
        )
        
        # Query the created schedule entry
        response = self.trading_configurations_table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :schedule_prefix)',
            ExpressionAttributeValues={
                ':user_id': self.test_user_id,
                ':schedule_prefix': f'SCHEDULE#{strategy_id}#WED#ENTRY'
            }
        )
        
        items = response.get('Items', [])
        self.assertEqual(len(items), 1, "Should find exactly one Wednesday entry schedule")
        
        schedule_item = items[0]
        execution_key = schedule_item['execution_schedule_key']
        
        # Verify format: ENTRY#{weekday}#{time}#{strategy_id}
        expected_key = f"ENTRY#WED#11:45#{strategy_id}"
        self.assertEqual(execution_key, expected_key,
                        f"Execution schedule key format incorrect. Expected: {expected_key}, Got: {execution_key}")
                        
    def test_different_underlyings_maintain_weekday_logic(self):
        """Test that different underlyings all maintain proper weekday logic"""
        
        underlyings = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
        entry_time = "13:15"
        entry_days = ['TUESDAY', 'THURSDAY']
        
        strategies = []
        
        # Create strategies for different underlyings
        for underlying in underlyings:
            if underlying == 'NIFTY':
                strategy_id = self.create_iron_condor_strategy(
                    strategy_name=f"{underlying} Weekday Test",
                    underlying=underlying,
                    entry_days=entry_days,
                    entry_time=entry_time
                )
            else:
                strategy_id = self.create_sample_strategy(
                    strategy_name=f"{underlying} Weekday Test",
                    underlying=underlying,
                    entry_days=entry_days,
                    entry_time=entry_time
                )
            
            strategies.append((underlying, strategy_id))
            
        # Verify Tuesday discovery finds all strategies
        tuesday_strategies = self.query_strategies_for_execution('TUE', entry_time)
        found_underlyings = {s['underlying'] for s in tuesday_strategies}
        
        for underlying in underlyings:
            self.assertIn(underlying, found_underlyings,
                         f"Tuesday query should find {underlying} strategy")
                         
        # Verify Wednesday discovery finds none of these strategies
        wednesday_strategies = self.query_strategies_for_execution('WED', entry_time)
        wed_strategy_ids = {s['strategy_id'] for s in wednesday_strategies}
        
        for underlying, strategy_id in strategies:
            self.assertNotIn(strategy_id, wed_strategy_ids,
                           f"Wednesday query should NOT find {underlying} strategy {strategy_id}")
                           
    def test_query_performance_with_weekday_filtering(self):
        """Test that weekday filtering improves query performance"""
        
        # Create multiple strategies across different weekdays and times
        import time
        
        # Create strategies for performance testing
        for weekday in ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']:
            for hour in [9, 10, 11, 14, 15]:
                for minute in [0, 15, 30, 45]:
                    entry_time = f"{hour:02d}:{minute:02d}"
                    self.create_sample_strategy(
                        strategy_name=f"Perf Test {weekday} {entry_time}",
                        entry_days=[weekday],
                        entry_time=entry_time
                    )
                    
        # Measure query performance with weekday filtering
        start_time = time.time()
        monday_strategies = self.query_strategies_for_execution('MON', '09:30')
        weekday_query_time = time.time() - start_time
        
        # Query should complete quickly (under 100ms in test environment)
        self.assertLess(weekday_query_time, 0.1,
                       f"Weekday-filtered query took {weekday_query_time:.3f}s, should be under 0.1s")
                       
        # Verify we got reasonable results
        self.assertGreater(len(monday_strategies), 0,
                          "Should find at least one Monday 09:30 strategy")
                          
    def test_edge_case_midnight_time_handling(self):
        """Test edge case handling for midnight and near-midnight times"""
        
        # Test strategies at edge times
        edge_times = ['00:00', '00:15', '23:45', '23:59']
        
        for edge_time in edge_times:
            strategy_id = self.create_sample_strategy(
                strategy_name=f"Edge Time Test {edge_time}",
                entry_days=['FRIDAY'],
                entry_time=edge_time
            )
            
            # Verify schedule was created correctly
            friday_strategies = self.query_strategies_for_execution('FRI', edge_time)
            strategy_ids = {s['strategy_id'] for s in friday_strategies}
            
            self.assertIn(strategy_id, strategy_ids,
                         f"Friday {edge_time} strategy should be discoverable")


if __name__ == '__main__':
    unittest.main()