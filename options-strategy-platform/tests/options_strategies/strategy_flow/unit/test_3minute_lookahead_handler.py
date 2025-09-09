"""
Test cases for 3-minute lookahead lambda handler functionality
Tests the main lambda_handler() function with 3-minute window calculation and processing
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os
import sys

# Add the project root to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../'))

# Import the function under test
from lambda_functions.option_baskets.schedule_strategy_trigger import lambda_handler

# Import test fixtures
from tests.options_strategies.strategy_flow.unit.fixtures.test_event_payloads import (
    VALID_3MIN_EVENT, VALID_5MIN_EVENT, INVALID_EVENT_MISSING_FIELDS, 
    INVALID_EVENT_BAD_TIME, WEEKEND_EVENT, EMPTY_EVENT, NO_DETAIL_EVENT
)
from tests.options_strategies.strategy_flow.unit.fixtures.test_strategy_data import (
    SAMPLE_STRATEGY_12_01, SAMPLE_STRATEGY_12_03, MULTIPLE_STRATEGIES_DIFFERENT_TIMES,
    EXPECTED_SQS_MESSAGE_STRUCTURE, EXPECTED_MESSAGE_ATTRIBUTES
)
from tests.options_strategies.strategy_flow.unit.fixtures.test_dynamodb_responses import (
    SUCCESSFUL_GSI4_RESPONSE_WITH_STRATEGIES, EMPTY_GSI4_RESPONSE, 
    SUCCESSFUL_SQS_RESPONSE, SQS_ERROR_RESPONSE
)


class TestThreeMinuteLookaheadHandler:
    """Test cases for the main 3-minute lookahead lambda handler"""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Set up environment variables for testing"""
        os.environ['TRADING_CONFIGURATIONS_TABLE'] = 'test-trading-configurations'
        os.environ['SINGLE_STRATEGY_QUEUE_URL'] = 'https://sqs.amazonaws.com/test-queue'
        os.environ['REGION'] = 'ap-south-1'
        
    @pytest.fixture
    def mock_context(self):
        """Mock Lambda context"""
        context = Mock()
        context.function_name = 'test-schedule-strategy-trigger'
        context.aws_request_id = 'test-request-id'
        return context
        
    @pytest.fixture
    def mock_dynamodb_table(self):
        """Mock DynamoDB table"""
        table = Mock()
        return table
        
    @pytest.fixture
    def mock_sqs_client(self):
        """Mock SQS client"""
        sqs = Mock()
        sqs.send_message.return_value = SUCCESSFUL_SQS_RESPONSE
        return sqs

    @patch('lambda_functions.option_baskets.schedule_strategy_trigger.boto3')
    def test_successful_3minute_lookahead_with_strategies(self, mock_boto3, mock_context, 
                                                         mock_dynamodb_table, mock_sqs_client):
        """Test successful 3-minute lookahead processing with strategies found"""
        # Setup mocks
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_boto3.client.return_value = mock_sqs_client
        
        # Mock DynamoDB table query to return strategies for specific times
        def query_side_effect(**kwargs):
            schedule_pattern = kwargs['ExpressionAttributeValues'][':pattern']
            if '12:01' in schedule_pattern:
                return SUCCESSFUL_GSI4_RESPONSE_WITH_STRATEGIES
            elif '12:03' in schedule_pattern:
                return SUCCESSFUL_GSI4_RESPONSE_WITH_STRATEGIES  
            else:
                return EMPTY_GSI4_RESPONSE
        
        mock_dynamodb_table.query.side_effect = query_side_effect
        
        # Execute
        result = lambda_handler(VALID_3MIN_EVENT, mock_context)
        
        # Assertions
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        
        assert response_body['success'] is True
        assert response_body['user_id'] == 'user_test_001'
        assert response_body['lookahead_window'] == ['12:01', '12:02', '12:03']
        assert response_body['strategies_found'] == 4  # 2 strategies for 12:01 + 2 for 12:03
        assert response_body['strategies_processed'] == 4
        assert response_body['architecture'] == 'USER_SPECIFIC_3MIN_LOOKAHEAD_GSI4_QUERY'
        
        # Verify SQS calls
        assert mock_sqs_client.send_message.call_count == 4
        
        # Verify table query calls (once for each minute in window)
        assert mock_dynamodb_table.query.call_count == 3
            
    @patch('lambda_functions.option_baskets.schedule_strategy_trigger.boto3')
    def test_3minute_lookahead_no_strategies_found(self, mock_boto3, mock_context,
                                                  mock_dynamodb_table, mock_sqs_client):
        """Test 3-minute lookahead when no strategies are found"""
        # Setup mocks
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_boto3.client.return_value = mock_sqs_client
        
        # Mock discover to return empty results
        with patch('lambda_functions.option_baskets.schedule_strategy_trigger.discover_user_strategies_for_schedule', return_value=[]):
            # Execute
            result = lambda_handler(VALID_3MIN_EVENT, mock_context)
            
            # Assertions
            assert result['statusCode'] == 200
            response_body = json.loads(result['body'])
            
            assert response_body['success'] is True
            assert response_body['strategies_found'] == 0
            assert 'No strategies scheduled' in response_body['message']
            assert mock_sqs_client.send_message.call_count == 0

    def test_lookahead_window_calculation(self):
        """Test 3-minute lookahead window calculation logic"""
        # Test the window calculation logic directly
        from datetime import datetime, timedelta
        
        trigger_time = datetime.fromisoformat('2025-09-08T12:00:00')
        lookahead_minutes = 3
        
        execution_times = []
        for i in range(1, lookahead_minutes + 1):
            future_time = trigger_time + timedelta(minutes=i)
            execution_time_str = future_time.strftime("%H:%M")
            execution_times.append(execution_time_str)
        
        assert execution_times == ['12:01', '12:02', '12:03']
        
        # Test with different trigger time
        trigger_time = datetime.fromisoformat('2025-09-08T09:15:00')
        execution_times = []
        for i in range(1, lookahead_minutes + 1):
            future_time = trigger_time + timedelta(minutes=i)
            execution_time_str = future_time.strftime("%H:%M")
            execution_times.append(execution_time_str)
        
        assert execution_times == ['09:16', '09:17', '09:18']

    @patch('lambda_functions.option_baskets.schedule_strategy_trigger.boto3')
    def test_5minute_lookahead_window(self, mock_boto3, mock_context,
                                     mock_dynamodb_table, mock_sqs_client):
        """Test 5-minute lookahead window (different from default 3-minute)"""
        # Setup mocks
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_boto3.client.return_value = mock_sqs_client
        
        with patch('lambda_functions.option_baskets.schedule_strategy_trigger.discover_user_strategies_for_schedule', return_value=[]):
            # Execute with 5-minute event
            result = lambda_handler(VALID_5MIN_EVENT, mock_context)
            
            # Assertions
            assert result['statusCode'] == 200
            response_body = json.loads(result['body'])
            
            # Should create 5-minute window: 14:16, 14:17, 14:18, 14:19, 14:20
            expected_window = ['14:16', '14:17', '14:18', '14:19', '14:20']
            assert response_body['lookahead_window'] == expected_window

    @patch('lambda_functions.option_baskets.schedule_strategy_trigger.boto3')
    def test_missing_sqs_queue_configuration(self, mock_boto3, mock_context,
                                           mock_dynamodb_table, mock_sqs_client):
        """Test error handling when SQS queue URL is not configured"""
        # Remove SQS queue environment variable
        if 'SINGLE_STRATEGY_QUEUE_URL' in os.environ:
            del os.environ['SINGLE_STRATEGY_QUEUE_URL']
            
        # Setup mocks
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        
        # Mock DynamoDB table query to return strategies
        mock_dynamodb_table.query.return_value = {'Items': [SAMPLE_STRATEGY_12_01], 'Count': 1, 'ScannedCount': 1}
        
        # Execute
        result = lambda_handler(VALID_3MIN_EVENT, mock_context)
        
        # Assertions
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert 'SQS Queue URL not configured' in response_body['error']
            
        # Restore environment variable
        os.environ['SINGLE_STRATEGY_QUEUE_URL'] = 'https://sqs.amazonaws.com/test-queue'

    @patch('lambda_functions.option_baskets.schedule_strategy_trigger.boto3')
    def test_partial_sqs_failures(self, mock_boto3, mock_context,
                                 mock_dynamodb_table, mock_sqs_client):
        """Test handling of partial SQS send failures"""
        # Setup mocks - make second SQS call fail
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_boto3.client.return_value = mock_sqs_client
        
        # Mock SQS to succeed first, fail second
        mock_sqs_client.send_message.side_effect = [
            SUCCESSFUL_SQS_RESPONSE,  # First call succeeds
            Exception("SQS send failed")  # Second call fails
        ]
        
        # Mock DynamoDB table query to return strategies for specific times
        def query_side_effect(**kwargs):
            schedule_pattern = kwargs['ExpressionAttributeValues'][':pattern']
            if '12:01' in schedule_pattern:
                return {'Items': [SAMPLE_STRATEGY_12_01], 'Count': 1, 'ScannedCount': 1}
            elif '12:03' in schedule_pattern:
                return {'Items': [SAMPLE_STRATEGY_12_03], 'Count': 1, 'ScannedCount': 1}
            else:
                return EMPTY_GSI4_RESPONSE
        
        mock_dynamodb_table.query.side_effect = query_side_effect
        
        # Execute
        result = lambda_handler(VALID_3MIN_EVENT, mock_context)
        
        # Assertions
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        
        assert response_body['strategies_found'] == 2
        assert response_body['strategies_processed'] == 1  # Only one succeeded
        
        # Check SQS results contain both success and error
        sqs_results = response_body['sqs_results']
        assert len(sqs_results) == 2
        assert any(r['status'] == 'success' for r in sqs_results)
        assert any(r['status'] == 'error' for r in sqs_results)

    def test_invalid_event_missing_fields(self, mock_context):
        """Test handling of invalid event with missing required fields"""
        result = lambda_handler(INVALID_EVENT_MISSING_FIELDS, mock_context)
        
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert 'error' in response_body

    def test_invalid_event_bad_time_format(self, mock_context):
        """Test handling of invalid trigger time format"""
        result = lambda_handler(INVALID_EVENT_BAD_TIME, mock_context)
        
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert 'error' in response_body

    def test_empty_event_handling(self, mock_context):
        """Test handling of empty event"""
        result = lambda_handler(EMPTY_EVENT, mock_context)
        
        assert result['statusCode'] == 500
        
    def test_no_detail_event_handling(self, mock_context):
        """Test handling of event with no detail field"""
        result = lambda_handler(NO_DETAIL_EVENT, mock_context)
        
        assert result['statusCode'] == 500

    @patch('lambda_functions.option_baskets.schedule_strategy_trigger.boto3')
    def test_sqs_message_structure_validation(self, mock_boto3, mock_context,
                                            mock_dynamodb_table, mock_sqs_client):
        """Test that SQS messages have correct structure and attributes"""
        # Setup mocks
        mock_boto3.resource.return_value.Table.return_value = mock_dynamodb_table
        mock_boto3.client.return_value = mock_sqs_client
        
        # Mock DynamoDB table query to return strategies for 12:01 only
        def query_side_effect(**kwargs):
            schedule_pattern = kwargs['ExpressionAttributeValues'][':pattern']
            if '12:01' in schedule_pattern:
                return {'Items': [SAMPLE_STRATEGY_12_01], 'Count': 1, 'ScannedCount': 1}
            else:
                return EMPTY_GSI4_RESPONSE
        
        mock_dynamodb_table.query.side_effect = query_side_effect
        
        # Execute
        result = lambda_handler(VALID_3MIN_EVENT, mock_context)
        
        # Verify SQS was called with correct structure
        assert mock_sqs_client.send_message.call_count == 1
        call_args = mock_sqs_client.send_message.call_args
        
        # Check message body structure
        message_body = json.loads(call_args[1]['MessageBody'])
        
        assert message_body['user_id'] == 'user_test_001'
        assert message_body['strategy_id'] == SAMPLE_STRATEGY_12_01['strategy_id']
        assert message_body['execution_time'] == '12:01'  # Scheduled time
        assert message_body['weekday'] == 'MON'
        assert message_body['trigger_source'] == 'user_specific_3min_lookahead_discovery'
        assert message_body['lookahead_window'] == ['12:01', '12:02', '12:03']
        
        # Check message attributes
        message_attrs = call_args[1]['MessageAttributes']
        assert message_attrs['UserId']['StringValue'] == 'user_test_001'
        assert message_attrs['StrategyId']['StringValue'] == SAMPLE_STRATEGY_12_01['strategy_id']
        assert message_attrs['ExecutionTime']['StringValue'] == '12:01'
        assert message_attrs['LookaheadWindow']['StringValue'] == '12:01,12:02,12:03'

    @patch('lambda_functions.option_baskets.schedule_strategy_trigger.boto3')
    def test_dynamodb_connection_failure(self, mock_boto3, mock_context):
        """Test handling of DynamoDB connection failures"""
        # Mock DynamoDB to raise an exception
        mock_boto3.resource.side_effect = Exception("DynamoDB connection failed")
        
        # Execute
        result = lambda_handler(VALID_3MIN_EVENT, mock_context)
        
        # Should return error response
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert 'error' in response_body


if __name__ == '__main__':
    pytest.main([__file__, '-v'])