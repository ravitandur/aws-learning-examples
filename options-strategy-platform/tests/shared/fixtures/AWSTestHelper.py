import boto3
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from moto import mock_events, mock_stepfunctions, mock_lambda
import uuid


class AWSTestHelper:
    """
    Helper class for AWS service testing utilities.
    Provides mocking and testing capabilities for EventBridge, Step Functions, and Lambda.
    """
    
    def __init__(self, region: str = 'ap-south-1'):
        self.region = region
        self.events_client = None
        self.stepfunctions_client = None
        self.lambda_client = None
        
    def setup_eventbridge_mock(self):
        """Set up EventBridge mock client"""
        self.events_client = boto3.client('events', region_name=self.region)
        
    def setup_stepfunctions_mock(self):
        """Set up Step Functions mock client"""
        self.stepfunctions_client = boto3.client('stepfunctions', region_name=self.region)
        
    def setup_lambda_mock(self):
        """Set up Lambda mock client"""
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        
    def create_mock_eventbridge_rule(self, rule_name: str, event_pattern: Dict[str, Any]) -> str:
        """Create a mock EventBridge rule for testing"""
        if not self.events_client:
            self.setup_eventbridge_mock()
            
        response = self.events_client.put_rule(
            Name=rule_name,
            EventPattern=json.dumps(event_pattern),
            State='ENABLED',
            Description=f'Test rule: {rule_name}'
        )
        
        return response['RuleArn']
        
    def emit_test_eventbridge_event(self, 
                                  source: str,
                                  detail_type: str, 
                                  detail: Dict[str, Any]) -> str:
        """Emit a test EventBridge event"""
        if not self.events_client:
            self.setup_eventbridge_mock()
            
        response = self.events_client.put_events(
            Entries=[{
                'Source': source,
                'DetailType': detail_type,
                'Detail': json.dumps(detail, default=str),
                'Time': datetime.now(timezone.utc)
            }]
        )
        
        return response['Entries'][0]['EventId']
        
    def create_strategy_execution_event(self, 
                                      strategies: List[Dict],
                                      execution_time: str,
                                      wait_seconds: int,
                                      market_phase: str = 'ACTIVE_TRADING') -> Dict[str, Any]:
        """Create a strategy execution trigger event for testing"""
        return {
            'event_id': str(uuid.uuid4()),
            'event_type': 'TRIGGER_STRATEGY_EXECUTION',
            'execution_time': execution_time,
            'execution_datetime': datetime.now(timezone.utc).isoformat(),
            'wait_seconds': wait_seconds,
            'strategies': strategies,
            'strategy_count': len(strategies),
            'market_phase': market_phase,
            'trigger_source': 'schedule_strategy_trigger_test',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'step_function_trigger': {
                'type': 'EXPRESS_EXECUTION',
                'priority': 'HIGH' if market_phase in ['MARKET_OPEN', 'PRE_CLOSE'] else 'NORMAL'
            }
        }
        
    def create_schedule_strategy_trigger_event(self,
                                             discovery_window_start: str,
                                             discovery_window_end: str,
                                             market_phase: str = 'ACTIVE_TRADING') -> Dict[str, Any]:
        """Create a schedule strategy trigger event for testing"""
        return {
            'event_id': str(uuid.uuid4()),
            'trigger_time_ist': datetime.now(timezone.utc).strftime('%H:%M'),
            'market_phase': market_phase,
            'discovery_window_start': discovery_window_start,
            'discovery_window_end': discovery_window_end,
            'expected_strategy_volume': 'MEDIUM',
            'query_optimization': 'GSI2_UserExecutionSchedule'
        }
        
    def create_mock_step_function(self, name: str, definition: Dict[str, Any]) -> str:
        """Create a mock Step Function for testing"""
        if not self.stepfunctions_client:
            self.setup_stepfunctions_mock()
            
        response = self.stepfunctions_client.create_state_machine(
            name=name,
            definition=json.dumps(definition),
            roleArn=f'arn:aws:iam::123456789012:role/test-role',
            type='EXPRESS'
        )
        
        return response['stateMachineArn']
        
    def start_step_function_execution(self, 
                                    state_machine_arn: str,
                                    execution_input: Dict[str, Any]) -> str:
        """Start a Step Function execution for testing"""
        if not self.stepfunctions_client:
            self.setup_stepfunctions_mock()
            
        response = self.stepfunctions_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=f'test-execution-{uuid.uuid4()}',
            input=json.dumps(execution_input, default=str)
        )
        
        return response['executionArn']
        
    def get_step_function_execution_result(self, execution_arn: str) -> Dict[str, Any]:
        """Get Step Function execution result for testing"""
        if not self.stepfunctions_client:
            self.setup_stepfunctions_mock()
            
        response = self.stepfunctions_client.describe_execution(
            executionArn=execution_arn
        )
        
        return response
        
    def create_mock_lambda_function(self, 
                                  function_name: str,
                                  handler: str = 'index.handler',
                                  runtime: str = 'python3.11') -> str:
        """Create a mock Lambda function for testing"""
        if not self.lambda_client:
            self.setup_lambda_mock()
            
        # Create a simple Lambda function code
        zip_content = b'fake lambda code'
        
        response = self.lambda_client.create_function(
            FunctionName=function_name,
            Runtime=runtime,
            Role=f'arn:aws:iam::123456789012:role/test-lambda-role',
            Handler=handler,
            Code={'ZipFile': zip_content},
            Description=f'Test Lambda function: {function_name}',
            Timeout=30,
            MemorySize=256
        )
        
        return response['FunctionArn']
        
    def invoke_mock_lambda(self, 
                         function_name: str,
                         payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a mock Lambda function for testing"""
        if not self.lambda_client:
            self.setup_lambda_mock()
            
        response = self.lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload, default=str)
        )
        
        return {
            'StatusCode': response['StatusCode'],
            'Payload': json.loads(response['Payload'].read().decode())
        }
        
    def validate_eventbridge_event_format(self, event: Dict[str, Any], expected_fields: List[str]) -> bool:
        """Validate that EventBridge event has required fields"""
        for field in expected_fields:
            if field not in event:
                return False
        return True
        
    def create_weekday_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create test scenarios for weekday validation"""
        return [
            {
                'name': 'monday_morning_execution',
                'weekday': 'MON',
                'execution_time': '09:30',
                'should_execute': True,
                'description': 'Monday morning strategy should execute'
            },
            {
                'name': 'friday_afternoon_execution', 
                'weekday': 'FRI',
                'execution_time': '15:20',
                'should_execute': True,
                'description': 'Friday afternoon exit should execute'
            },
            {
                'name': 'saturday_morning_execution',
                'weekday': 'SAT', 
                'execution_time': '09:30',
                'should_execute': False,
                'description': 'Saturday execution should be skipped'
            },
            {
                'name': 'sunday_evening_execution',
                'weekday': 'SUN',
                'execution_time': '18:00', 
                'should_execute': False,
                'description': 'Sunday execution should be skipped'
            }
        ]
        
    def create_overlap_prevention_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create test scenarios for overlap prevention (18:20 window issue)"""
        return [
            {
                'name': 'window_18_15_to_18_20',
                'discovery_start': '2025-09-04T18:15:00.000000+05:30',
                'discovery_end': '2025-09-04T18:20:00.000000+05:30',
                'expected_minutes': ['18:15', '18:16', '18:17', '18:18', '18:19'],
                'should_include_18_20': False,
                'description': 'First window should not include 18:20'
            },
            {
                'name': 'window_18_20_to_18_25', 
                'discovery_start': '2025-09-04T18:20:00.000000+05:30',
                'discovery_end': '2025-09-04T18:25:00.000000+05:30',
                'expected_minutes': ['18:20', '18:21', '18:22', '18:23', '18:24'],
                'should_include_18_20': True,
                'description': 'Second window should include 18:20'
            }
        ]