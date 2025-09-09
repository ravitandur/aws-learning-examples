"""
Test cases for GSI4 strategy discovery functionality
Tests the discover_user_strategies_for_schedule() function and GSI4 query patterns
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../'))

# Import the function under test
from lambda_functions.option_baskets.schedule_strategy_trigger import discover_user_strategies_for_schedule

# Import test fixtures
from tests.options_strategies.strategy_flow.unit.fixtures.test_strategy_data import (
    SAMPLE_STRATEGY_12_01, SAMPLE_STRATEGY_12_03, EXIT_STRATEGY, MINIMAL_STRATEGY
)
from tests.options_strategies.strategy_flow.unit.fixtures.test_dynamodb_responses import (
    SUCCESSFUL_GSI4_RESPONSE_WITH_STRATEGIES, EMPTY_GSI4_RESPONSE, 
    SINGLE_STRATEGY_RESPONSE, EXIT_STRATEGY_RESPONSE, MINIMAL_STRATEGY_RESPONSE,
    THROTTLING_EXCEPTION, VALIDATION_EXCEPTION, EXPECTED_GSI4_QUERY_PARAMS
)


class TestGSI4StrategyDiscovery:
    """Test cases for GSI4 strategy discovery function"""
    
    @pytest.fixture
    def mock_trading_table(self):
        """Mock DynamoDB trading configurations table"""
        table = Mock()
        return table

    def test_successful_strategy_discovery_single_time(self, mock_trading_table):
        """Test successful strategy discovery for a single execution time"""
        # Setup mock response
        mock_trading_table.query.return_value = SINGLE_STRATEGY_RESPONSE
        
        # Execute
        strategies = discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '12:01', 'MON'
        )
        
        # Assertions
        assert len(strategies) == 1
        strategy = strategies[0]
        
        assert strategy['user_id'] == 'user_test_001'
        assert strategy['strategy_id'] == SAMPLE_STRATEGY_12_01['strategy_id']
        assert strategy['strategy_name'] == SAMPLE_STRATEGY_12_01['strategy_name']
        assert strategy['execution_time'] == '12:01'
        assert strategy['execution_type'] == 'ENTRY'  # Derived from sort_key
        
        # Verify GSI4 query was called with correct parameters
        mock_trading_table.query.assert_called_once()
        call_args = mock_trading_table.query.call_args[1]
        
        assert call_args['IndexName'] == 'UserScheduleDiscovery'
        assert call_args['KeyConditionExpression'] == 'user_id = :user_id AND begins_with(schedule_key, :pattern)'
        assert call_args['ExpressionAttributeValues'][':user_id'] == 'user_test_001'
        assert call_args['ExpressionAttributeValues'][':pattern'] == 'SCHEDULE#MON#12:01'
        assert call_args['ExpressionAttributeValues'][':active'] == 'ACTIVE'

    def test_successful_strategy_discovery_multiple_strategies(self, mock_trading_table):
        """Test discovery with multiple strategies returned"""
        # Setup mock response with multiple strategies
        mock_trading_table.query.return_value = SUCCESSFUL_GSI4_RESPONSE_WITH_STRATEGIES
        
        # Execute
        strategies = discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '12:01', 'MON'
        )
        
        # Assertions
        assert len(strategies) == 2
        
        # Check first strategy
        strategy1 = strategies[0]
        assert strategy1['strategy_id'] == SAMPLE_STRATEGY_12_01['strategy_id']
        assert strategy1['execution_type'] == 'ENTRY'
        
        # Check second strategy
        strategy2 = strategies[1]
        assert strategy2['strategy_id'] == SAMPLE_STRATEGY_12_03['strategy_id']
        assert strategy2['execution_type'] == 'ENTRY'

    def test_empty_strategy_discovery(self, mock_trading_table):
        """Test when no strategies are found for the given time"""
        # Setup mock response with empty results
        mock_trading_table.query.return_value = EMPTY_GSI4_RESPONSE
        
        # Execute
        strategies = discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '12:05', 'MON'
        )
        
        # Assertions
        assert len(strategies) == 0
        
        # Verify query was still called
        mock_trading_table.query.assert_called_once()

    def test_exit_strategy_detection(self, mock_trading_table):
        """Test proper detection of EXIT strategies vs ENTRY strategies"""
        # Setup mock response with EXIT strategy
        mock_trading_table.query.return_value = EXIT_STRATEGY_RESPONSE
        
        # Execute
        strategies = discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '15:20', 'MON'
        )
        
        # Assertions
        assert len(strategies) == 1
        strategy = strategies[0]
        
        assert strategy['execution_type'] == 'EXIT'  # Should detect EXIT from sort_key
        assert strategy['strategy_id'] == 'strategy-exit-001'

    def test_schedule_pattern_construction(self, mock_trading_table):
        """Test correct schedule pattern construction for different weekdays and times"""
        mock_trading_table.query.return_value = EMPTY_GSI4_RESPONSE
        
        test_cases = [
            ('user_001', '09:15', 'MON', 'SCHEDULE#MON#09:15'),
            ('user_002', '15:20', 'FRI', 'SCHEDULE#FRI#15:20'),
            ('user_003', '12:30', 'WED', 'SCHEDULE#WED#12:30'),
        ]
        
        for user_id, execution_time, weekday, expected_pattern in test_cases:
            # Reset mock
            mock_trading_table.query.reset_mock()
            
            # Execute
            discover_user_strategies_for_schedule(
                mock_trading_table, user_id, execution_time, weekday
            )
            
            # Verify correct pattern was used
            call_args = mock_trading_table.query.call_args[1]
            assert call_args['ExpressionAttributeValues'][':pattern'] == expected_pattern
            assert call_args['ExpressionAttributeValues'][':user_id'] == user_id

    def test_minimal_strategy_data_handling(self, mock_trading_table):
        """Test handling of strategies with minimal/missing optional fields"""
        # Setup mock response with minimal strategy
        mock_trading_table.query.return_value = MINIMAL_STRATEGY_RESPONSE
        
        # Execute
        strategies = discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '12:01', 'MON'
        )
        
        # Assertions
        assert len(strategies) == 1
        strategy = strategies[0]
        
        assert strategy['strategy_id'] == 'strategy-minimal-001'
        assert strategy['execution_type'] == 'ENTRY'
        
        # Optional fields should have default values
        assert strategy['weekdays'] == []
        assert strategy['legs'] == []
        assert strategy['underlying'] is None
        assert strategy['strategy_type'] is None

    def test_projection_expression_fields(self, mock_trading_table):
        """Test that the correct fields are projected from GSI4"""
        mock_trading_table.query.return_value = EMPTY_GSI4_RESPONSE
        
        # Execute
        discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '12:01', 'MON'
        )
        
        # Verify projection expression includes all required fields
        call_args = mock_trading_table.query.call_args[1]
        projection_expr = call_args['ProjectionExpression']
        
        required_fields = [
            'strategy_id', 'strategy_name', 'execution_time', 'weekdays',
            'legs', 'underlying', 'strategy_type', 'sort_key', 'schedule_key'
        ]
        
        for field in required_fields:
            assert field in projection_expr

    def test_status_filter_expression(self, mock_trading_table):
        """Test that only ACTIVE strategies are filtered"""
        mock_trading_table.query.return_value = EMPTY_GSI4_RESPONSE
        
        # Execute
        discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '12:01', 'MON'
        )
        
        # Verify filter expression and attribute names
        call_args = mock_trading_table.query.call_args[1]
        
        assert call_args['FilterExpression'] == '#status = :active'
        assert call_args['ExpressionAttributeNames']['#status'] == 'status'
        assert call_args['ExpressionAttributeValues'][':active'] == 'ACTIVE'

    def test_dynamodb_throttling_exception(self, mock_trading_table):
        """Test handling of DynamoDB throttling exceptions"""
        from botocore.exceptions import ClientError
        
        # Setup mock to raise throttling exception
        mock_trading_table.query.side_effect = ClientError(
            THROTTLING_EXCEPTION, 'Query'
        )
        
        # Execute - should handle exception gracefully
        strategies = discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '12:01', 'MON'
        )
        
        # Should return empty list on error
        assert strategies == []

    def test_dynamodb_validation_exception(self, mock_trading_table):
        """Test handling of DynamoDB validation exceptions"""
        from botocore.exceptions import ClientError
        
        # Setup mock to raise validation exception
        mock_trading_table.query.side_effect = ClientError(
            VALIDATION_EXCEPTION, 'Query'
        )
        
        # Execute - should handle exception gracefully
        strategies = discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '12:01', 'MON'
        )
        
        # Should return empty list on error
        assert strategies == []

    def test_general_exception_handling(self, mock_trading_table):
        """Test handling of general exceptions during query"""
        # Setup mock to raise general exception
        mock_trading_table.query.side_effect = Exception("Unexpected error")
        
        # Execute - should handle exception gracefully
        strategies = discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '12:01', 'MON'
        )
        
        # Should return empty list on error
        assert strategies == []

    def test_performance_optimization_verification(self, mock_trading_table):
        """Test that the function uses efficient GSI4 QUERY (not SCAN)"""
        mock_trading_table.query.return_value = EMPTY_GSI4_RESPONSE
        
        # Execute
        discover_user_strategies_for_schedule(
            mock_trading_table, 'user_test_001', '12:01', 'MON'
        )
        
        # Verify QUERY was called (not scan)
        mock_trading_table.query.assert_called_once()
        mock_trading_table.scan.assert_not_called()
        
        # Verify it's using the correct GSI
        call_args = mock_trading_table.query.call_args[1]
        assert call_args['IndexName'] == 'UserScheduleDiscovery'

    def test_weekday_case_sensitivity(self, mock_trading_table):
        """Test that weekday parameter is handled correctly regardless of case"""
        mock_trading_table.query.return_value = EMPTY_GSI4_RESPONSE
        
        test_cases = ['MON', 'mon', 'Mon', 'MONDAY']
        
        for weekday in test_cases:
            mock_trading_table.query.reset_mock()
            
            # Execute
            discover_user_strategies_for_schedule(
                mock_trading_table, 'user_test_001', '12:01', weekday
            )
            
            # Verify pattern uses the weekday as provided (function should handle normalization)
            call_args = mock_trading_table.query.call_args[1]
            pattern = call_args['ExpressionAttributeValues'][':pattern']
            assert weekday in pattern

    def test_user_id_parameter_validation(self, mock_trading_table):
        """Test handling of different user ID formats"""
        mock_trading_table.query.return_value = EMPTY_GSI4_RESPONSE
        
        test_user_ids = [
            'user_001', 
            'user-with-hyphens',
            'userwithnumbers123',
            'User_With_Mixed_Case'
        ]
        
        for user_id in test_user_ids:
            mock_trading_table.query.reset_mock()
            
            # Execute
            discover_user_strategies_for_schedule(
                mock_trading_table, user_id, '12:01', 'MON'
            )
            
            # Verify user_id is passed correctly
            call_args = mock_trading_table.query.call_args[1]
            assert call_args['ExpressionAttributeValues'][':user_id'] == user_id


if __name__ == '__main__':
    pytest.main([__file__, '-v'])