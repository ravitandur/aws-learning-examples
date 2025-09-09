import unittest
import json
import boto3
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
from moto import mock_aws
import pytest


class BaseStrategyTestCase(unittest.TestCase):
    """
    Base test case for all strategy testing across different asset classes.
    
    Provides common infrastructure for:
    - AWS service mocking
    - Database setup and teardown  
    - Common test utilities
    - Strategy data validation
    - Market timing simulation
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level test infrastructure"""
        cls.aws_region = 'ap-south-1'
        cls.company_prefix = 'ql'
        cls.project_name = 'algo-trading'
        cls.test_env = 'test'
        
        # Test table names
        cls.trading_configurations_table_name = f"{cls.company_prefix}-{cls.project_name}-{cls.test_env}-trading-configurations"
        cls.execution_history_table_name = f"{cls.company_prefix}-{cls.project_name}-{cls.test_env}-execution-history"
        
    def setUp(self):
        """Set up test-specific infrastructure"""
        # Start AWS service mocks (modern moto approach)
        self.mock_aws = mock_aws()
        self.mock_aws.start()
        
        # Initialize AWS clients
        self.dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
        self.events_client = boto3.client('events', region_name=self.aws_region)
        self.stepfunctions_client = boto3.client('stepfunctions', region_name=self.aws_region)
        
        # Create test tables
        self.create_test_tables()
        
        # Set up test user
        self.test_user_id = 'test_user_123'
        self.test_basket_id = 'basket_456'
        
    def tearDown(self):
        """Clean up test infrastructure"""
        self.mock_aws.stop()
        
    def create_test_tables(self):
        """Create test DynamoDB tables with proper schema"""
        
        # Trading Configurations Table (Single Table Design)
        self.trading_configurations_table = self.dynamodb.create_table(
            TableName=self.trading_configurations_table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'sort_key', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'sort_key', 'AttributeType': 'S'},
                {'AttributeName': 'basket_id', 'AttributeType': 'S'},
                {'AttributeName': 'entity_type_priority', 'AttributeType': 'S'},
                {'AttributeName': 'execution_schedule_key', 'AttributeType': 'S'},
                # GSI3 attributes for TimeBasedExecutionDiscovery
                {'AttributeName': 'execution_time_slot', 'AttributeType': 'S'},
                {'AttributeName': 'user_strategy_composite', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'AllocationsByBasket',
                    'KeySchema': [
                        {'AttributeName': 'basket_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'entity_type_priority', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'UserExecutionSchedule',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'execution_schedule_key', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'TimeBasedExecutionDiscovery',
                    'KeySchema': [
                        {'AttributeName': 'execution_time_slot', 'KeyType': 'HASH'},
                        {'AttributeName': 'user_strategy_composite', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Execution History Table
        self.execution_history_table = self.dynamodb.create_table(
            TableName=self.execution_history_table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'execution_key', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'execution_key', 'AttributeType': 'S'},
                {'AttributeName': 'strategy_id', 'AttributeType': 'S'},
                {'AttributeName': 'execution_timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'execution_date', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'ExecutionsByStrategy',
                    'KeySchema': [
                        {'AttributeName': 'strategy_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'execution_timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'ExecutionsByDate',
                    'KeySchema': [
                        {'AttributeName': 'execution_date', 'KeyType': 'HASH'},
                        {'AttributeName': 'execution_timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for tables to be created
        self.trading_configurations_table.wait_until_exists()
        self.execution_history_table.wait_until_exists()
        
    def create_sample_basket(self, basket_name: str = "Test Basket") -> str:
        """Create a sample basket for testing"""
        basket_id = f"basket_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        basket_item = {
            'user_id': self.test_user_id,
            'sort_key': f'BASKET#{basket_id}',
            'basket_id': basket_id,
            'name': basket_name,
            'description': 'Test basket for automated testing',
            'status': 'ACTIVE',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        self.trading_configurations_table.put_item(Item=basket_item)
        return basket_id
        
    def create_sample_strategy(self, 
                             strategy_name: str = "Test Strategy",
                             underlying: str = "NIFTY",
                             entry_time: str = "09:30",
                             exit_time: str = "15:20",
                             entry_days: List[str] = None,
                             exit_days: List[str] = None,
                             legs: List[Dict] = None) -> str:
        """Create a sample strategy with weekday-aware scheduling"""
        
        if entry_days is None:
            entry_days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
        if exit_days is None:
            exit_days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
        if legs is None:
            legs = self.get_default_iron_condor_legs()
            
        strategy_id = f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Get lot size for the underlying
        lot_size_map = {
            'NIFTY': 25, 
            'BANKNIFTY': 15, 
            'FINNIFTY': 25,
            'MIDCPNIFTY': 75, 
            'SENSEX': 10
        }
        lot_size = lot_size_map.get(underlying, 25)  # Default to NIFTY lot size
        
        # Add expiry_date to legs if missing
        legs_with_expiry = []
        for leg in legs:
            leg_with_expiry = leg.copy()
            if 'expiry_date' not in leg_with_expiry:
                # Calculate next expiry based on underlying
                expiry_weekday_map = {
                    'NIFTY': 3,      # Thursday 
                    'BANKNIFTY': 2,  # Wednesday
                    'FINNIFTY': 1,   # Tuesday
                    'MIDCPNIFTY': 0, # Monday
                    'SENSEX': 4      # Friday
                }
                weekday = expiry_weekday_map.get(underlying, 3)
                next_expiry = self._get_next_expiry_date(weekday)
                leg_with_expiry['expiry_date'] = next_expiry.strftime('%Y-%m-%d')
            
            # Add lot_size to leg if missing
            if 'lot_size' not in leg_with_expiry:
                leg_with_expiry['lot_size'] = lot_size
                
            # Add underlying to leg if missing
            if 'underlying' not in leg_with_expiry:
                leg_with_expiry['underlying'] = underlying
                
            legs_with_expiry.append(leg_with_expiry)
        
        # Create main strategy record
        strategy_item = {
            'user_id': self.test_user_id,
            'sort_key': f'STRATEGY#{strategy_id}',
            'strategy_id': strategy_id,
            'basket_id': self.test_basket_id,
            'strategy_name': strategy_name,
            'description': 'Test strategy for automated testing',
            'underlying': underlying,
            'product': 'NRML',
            'lot_size': lot_size,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_days': entry_days,
            'exit_days': exit_days,
            'legs': legs_with_expiry,
            'status': 'ACTIVE',
            'created_at': current_time,
            'updated_at': current_time
        }
        
        self.trading_configurations_table.put_item(Item=strategy_item)
        
        # Create weekday-specific execution schedule entries
        weekday_abbr_map = {
            'MONDAY': 'MON', 'TUESDAY': 'TUE', 'WEDNESDAY': 'WED',
            'THURSDAY': 'THU', 'FRIDAY': 'FRI', 'SATURDAY': 'SAT', 'SUNDAY': 'SUN'
        }
        
        # Create ENTRY schedules
        for weekday in entry_days:
            weekday_abbr = weekday_abbr_map.get(weekday, weekday[:3].upper())
            
            entry_schedule_item = {
                'user_id': self.test_user_id,
                'sort_key': f'SCHEDULE#{strategy_id}#{weekday_abbr}#ENTRY',
                'strategy_id': strategy_id,
                'basket_id': self.test_basket_id,
                'strategy_name': strategy_name,
                'underlying': underlying,
                'product': 'NRML',
                'entry_time': entry_time,
                'weekday': weekday,
                'execution_type': 'ENTRY',
                'legs': legs,
                'execution_schedule_key': f"ENTRY#{weekday_abbr}#{entry_time}#{strategy_id}",
                # GSI3 attributes for TimeBasedExecutionDiscovery
                'execution_time_slot': entry_time,
                'user_strategy_composite': f"{self.test_user_id}#{strategy_id}#{entry_time}",
                'broker_allocation': self.get_default_broker_allocation(),
                'strategy_type': 'IRON_CONDOR',
                'weekdays': entry_days,
                'status': 'ACTIVE',
                'entity_type': 'EXECUTION_SCHEDULE',
                'created_at': current_time
            }
            
            self.trading_configurations_table.put_item(Item=entry_schedule_item)
            
        # Create EXIT schedules  
        for weekday in exit_days:
            weekday_abbr = weekday_abbr_map.get(weekday, weekday[:3].upper())
            
            exit_schedule_item = {
                'user_id': self.test_user_id,
                'sort_key': f'SCHEDULE#{strategy_id}#{weekday_abbr}#EXIT',
                'strategy_id': strategy_id,
                'basket_id': self.test_basket_id,
                'strategy_name': strategy_name,
                'underlying': underlying,
                'product': 'NRML',
                'exit_time': exit_time,
                'weekday': weekday,
                'execution_type': 'EXIT',
                'legs': legs,
                'execution_schedule_key': f"EXIT#{weekday_abbr}#{exit_time}#{strategy_id}",
                'status': 'ACTIVE',
                'entity_type': 'EXECUTION_SCHEDULE',
                'created_at': current_time
            }
            
            self.trading_configurations_table.put_item(Item=exit_schedule_item)
            
        return strategy_id
        
    def get_default_iron_condor_legs(self) -> List[Dict]:
        """Get default Iron Condor leg configuration for testing"""
        return [
            {
                'leg_id': 'leg_1',
                'option_type': 'PE',
                'strike_price': Decimal('19000'),
                'action': 'BUY',
                'quantity': 25,
                'order_type': 'MARKET'
            },
            {
                'leg_id': 'leg_2', 
                'option_type': 'PE',
                'strike_price': Decimal('19200'),
                'action': 'SELL',
                'quantity': 25,
                'order_type': 'MARKET'
            },
            {
                'leg_id': 'leg_3',
                'option_type': 'CE',
                'strike_price': Decimal('19800'),
                'action': 'SELL',
                'quantity': 25,
                'order_type': 'MARKET'
            },
            {
                'leg_id': 'leg_4',
                'option_type': 'CE',
                'strike_price': Decimal('20000'),
                'action': 'BUY',
                'quantity': 25,
                'order_type': 'MARKET'
            }
        ]
        
    def get_current_ist_time(self) -> datetime:
        """Get current IST time for testing"""
        utc_time = datetime.now(timezone.utc)
        ist_offset = timezone(timedelta(hours=5, minutes=30))
        return utc_time.astimezone(ist_offset)
        
    def get_weekday_abbr(self, weekday_full: str) -> str:
        """Convert full weekday name to abbreviation"""
        weekday_map = {
            'MONDAY': 'MON', 'TUESDAY': 'TUE', 'WEDNESDAY': 'WED',
            'THURSDAY': 'THU', 'FRIDAY': 'FRI', 'SATURDAY': 'SAT', 'SUNDAY': 'SUN'
        }
        return weekday_map.get(weekday_full.upper(), weekday_full[:3].upper())
        
    def query_strategies_for_execution(self, weekday: str, execution_time: str) -> List[Dict]:
        """Query strategies scheduled for execution at specific weekday and time"""
        response = self.trading_configurations_table.query(
            IndexName='UserExecutionSchedule',
            KeyConditionExpression='user_id = :user_id AND begins_with(execution_schedule_key, :schedule_prefix)',
            ExpressionAttributeValues={
                ':user_id': self.test_user_id,
                ':schedule_prefix': f'ENTRY#{weekday}#{execution_time}#'
            }
        )
        return response.get('Items', [])
        
    def assert_strategy_created_successfully(self, strategy_id: str, expected_schedules: int):
        """Assert that strategy and its schedules were created successfully"""
        
        # Check main strategy record
        strategy_response = self.trading_configurations_table.get_item(
            Key={
                'user_id': self.test_user_id,
                'sort_key': f'STRATEGY#{strategy_id}'
            }
        )
        self.assertIn('Item', strategy_response)
        self.assertEqual(strategy_response['Item']['strategy_id'], strategy_id)
        
        # Check schedule entries
        schedule_response = self.trading_configurations_table.query(
            KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :schedule_prefix)',
            ExpressionAttributeValues={
                ':user_id': self.test_user_id,
                ':schedule_prefix': f'SCHEDULE#{strategy_id}#'
            }
        )
        
        actual_schedules = len(schedule_response.get('Items', []))
        self.assertEqual(actual_schedules, expected_schedules, 
                        f"Expected {expected_schedules} schedule entries, found {actual_schedules}")
                        
    def assert_weekday_filtering_works(self, weekday: str, execution_time: str, expected_count: int):
        """Assert that weekday filtering returns expected number of strategies"""
        strategies = self.query_strategies_for_execution(weekday, execution_time)
        self.assertEqual(len(strategies), expected_count,
                        f"Expected {expected_count} strategies for {weekday} {execution_time}, found {len(strategies)}")
                        
    def get_default_broker_allocation(self) -> List[Dict]:
        """Get default broker allocation for testing GSI3 preloaded data"""
        return [
            {
                'broker_name': 'zerodha',
                'client_id': 'test_zerodha_001',
                'lot_size': 2,
                'allocation_id': 'alloc_zerodha_001',
                'priority': 1
            },
            {
                'broker_name': 'angelone', 
                'client_id': 'test_angelone_001',
                'lot_size': 1,
                'allocation_id': 'alloc_angelone_001',
                'priority': 2
            }
        ]
    
    def query_strategies_using_gsi3(self, execution_time: str) -> List[Dict]:
        """🚀 Query strategies using GSI3 TimeBasedExecutionDiscovery (Revolutionary optimization)"""
        response = self.trading_configurations_table.query(
            IndexName='TimeBasedExecutionDiscovery',
            KeyConditionExpression='execution_time_slot = :time_slot',
            ExpressionAttributeValues={
                ':time_slot': execution_time
            },
            ProjectionExpression='user_id, strategy_id, strategy_name, execution_time, legs, broker_allocation, weekdays, underlying, strategy_type'
        )
        return response.get('Items', [])
    
    def assert_gsi3_query_performance(self, execution_time: str, expected_strategies: int):
        """Assert GSI3 query returns expected number of strategies for time-based discovery"""
        strategies = self.query_strategies_using_gsi3(execution_time)
        self.assertEqual(len(strategies), expected_strategies,
                        f"GSI3 query for {execution_time} expected {expected_strategies} strategies, found {len(strategies)}")
        
        # Validate that all strategies have required GSI3 projection attributes
        for strategy in strategies:
            self.assertIn('broker_allocation', strategy, "GSI3 projection missing broker_allocation")
            self.assertIn('legs', strategy, "GSI3 projection missing legs")
            self.assertIn('strategy_type', strategy, "GSI3 projection missing strategy_type")
            
    def create_multi_user_test_data_for_gsi3(self, users_count: int = 3, strategies_per_user: int = 2) -> Dict[str, List[str]]:
        """Create test data for multiple users to test GSI3 multi-user discovery"""
        
        created_data = {'users': [], 'strategies': []}
        
        for user_idx in range(users_count):
            user_id = f'gsi3_test_user_{user_idx+1:03d}'
            created_data['users'].append(user_id)
            
            # Temporarily set test_user_id for this user's strategies
            original_user_id = self.test_user_id
            self.test_user_id = user_id
            
            for strategy_idx in range(strategies_per_user):
                strategy_id = self.create_sample_strategy(
                    strategy_name=f"GSI3 Test Strategy {user_idx+1}-{strategy_idx+1}",
                    entry_time="09:30",  # Same time slot for multi-user testing
                    underlying="NIFTY"
                )
                created_data['strategies'].append(strategy_id)
                
            # Restore original test user ID
            self.test_user_id = original_user_id
            
        return created_data
            
    def load_test_data_from_json(self, file_path: str) -> Dict[str, Any]:
        """Load test data from JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    # ✅ BASKET-LEVEL ALLOCATION METHODS (Industry Best Practice)
    def add_broker_allocation_to_basket(self,
                                      basket_id: str,
                                      broker_name: str,
                                      client_id: str,
                                      lot_multiplier: int,
                                      priority: int = 1) -> str:
        """Create basket-level broker allocation (strategies inherit from basket)"""
        
        allocation_id = f"alloc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        current_time = datetime.now(timezone.utc).isoformat()
        
        basket_allocation = {
            'user_id': self.test_user_id,
            'sort_key': f"BASKET_ALLOCATION#{allocation_id}",
            'entity_type': 'BASKET_ALLOCATION',
            'allocation_id': allocation_id,
            'basket_id': basket_id,
            'broker_name': broker_name,
            'client_id': client_id,
            'lot_multiplier': lot_multiplier,
            'priority': priority,
            'status': 'ACTIVE',
            'created_at': current_time,
            'updated_at': current_time,
            # For AllocationsByBasket GSI
            'entity_type_priority': f"BASKET_ALLOCATION#{priority:02d}#{allocation_id}"
        }
        
        self.trading_configurations_table.put_item(Item=basket_allocation)
        return allocation_id
    
    def get_basket_broker_allocations(self, basket_id: str) -> List[Dict]:
        """Get all broker allocations for a basket using AllocationsByBasket GSI"""
        
        response = self.trading_configurations_table.query(
            IndexName='AllocationsByBasket',
            KeyConditionExpression='basket_id = :basket_id AND begins_with(entity_type_priority, :allocation_prefix)',
            ExpressionAttributeValues={
                ':basket_id': basket_id,
                ':allocation_prefix': 'BASKET_ALLOCATION#'
            }
        )
        
        return response.get('Items', [])
    
    def calculate_total_lots_for_basket(self, basket_id: str) -> int:
        """Calculate total lot multiplier across all brokers for a basket"""
        
        allocations = self.get_basket_broker_allocations(basket_id)
        total_lots = sum(int(alloc.get('lot_multiplier', 0)) for alloc in allocations)
        
        return total_lots
    
    def modify_basket_broker_allocation(self,
                                      allocation_id: str,
                                      lot_multiplier: Optional[int] = None,
                                      client_id: Optional[str] = None,
                                      priority: Optional[int] = None):
        """Modify existing basket broker allocation"""
        
        # Get current allocation
        response = self.trading_configurations_table.get_item(
            Key={
                'user_id': self.test_user_id,
                'sort_key': f'BASKET_ALLOCATION#{allocation_id}'
            }
        )
        
        if 'Item' not in response:
            raise ValueError(f"Basket allocation {allocation_id} not found")
        
        item = response['Item']
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': datetime.now(timezone.utc).isoformat()}
        
        if lot_multiplier is not None:
            update_expression += ", lot_multiplier = :lot_multiplier"
            expression_values[':lot_multiplier'] = lot_multiplier
            
        if client_id is not None:
            update_expression += ", client_id = :client_id"
            expression_values[':client_id'] = client_id
            
        if priority is not None:
            update_expression += ", priority = :priority, entity_type_priority = :entity_type_priority"
            expression_values[':priority'] = priority
            expression_values[':entity_type_priority'] = f"BASKET_ALLOCATION#{priority:02d}#{allocation_id}"
        
        self.trading_configurations_table.update_item(
            Key={
                'user_id': self.test_user_id,
                'sort_key': f'BASKET_ALLOCATION#{allocation_id}'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
    
    def delete_basket_broker_allocation(self, allocation_id: str):
        """Delete basket broker allocation"""
        
        self.trading_configurations_table.delete_item(
            Key={
                'user_id': self.test_user_id,
                'sort_key': f'BASKET_ALLOCATION#{allocation_id}'
            }
        )
    
    # Legacy strategy-level allocation methods (for backward compatibility in tests that haven't been updated)
    def add_broker_allocation_to_strategy(self,
                                        strategy_id: str,
                                        broker_name: str,
                                        lots_allocation: int,
                                        leg_numbers: List[int]) -> str:
        """Legacy method - use add_broker_allocation_to_basket instead"""
        # For backward compatibility, just return a dummy allocation ID
        # Real implementation should use basket-level allocation
        return f"legacy_alloc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def get_strategy_broker_allocations(self, strategy_id: str) -> List[Dict]:
        """Legacy method - strategies inherit from basket allocations"""
        # For backward compatibility, return empty list
        # Tests should be updated to use get_basket_broker_allocations
        return []
    
    def calculate_total_lots_for_strategy(self, strategy_id: str) -> int:
        """Calculate total lots for strategy by inheriting from basket"""
        # Get strategy to find its basket_id
        strategy_response = self.trading_configurations_table.get_item(
            Key={
                'user_id': self.test_user_id,
                'sort_key': f'STRATEGY#{strategy_id}'
            }
        )
        
        if 'Item' not in strategy_response:
            return 0
        
        basket_id = strategy_response['Item'].get('basket_id')
        if not basket_id:
            return 0
        
        return self.calculate_total_lots_for_basket(basket_id)
    
    def modify_broker_allocation(self, allocation_id: str, lots_allocation: int, leg_numbers: List[int]):
        """Legacy method - use modify_basket_broker_allocation instead"""
        pass  # Legacy compatibility
    
    def delete_broker_allocation(self, allocation_id: str):
        """Legacy method - use delete_basket_broker_allocation instead"""
        pass  # Legacy compatibility
    
    def get_strategy_details(self, strategy_id: str) -> Dict:
        """Get complete strategy details with embedded legs data"""
        response = self.trading_configurations_table.get_item(
            Key={
                'user_id': self.test_user_id,
                'sort_key': f'STRATEGY#{strategy_id}'
            }
        )
        
        if 'Item' not in response:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        return response['Item']
    
    def _get_next_expiry_date(self, target_weekday: int) -> datetime:
        """Calculate next expiry date for given weekday (0=Monday, 6=Sunday)"""
        today = datetime.now().date()
        days_ahead = target_weekday - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return datetime.combine(today + timedelta(days=days_ahead), datetime.min.time())