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


class TestMultiBrokerExecutionFlow(OptionsStrategyTestBase):
    """
    Integration test for multi-broker execution workflow - the platform's revolutionary feature.
    
    Tests the complete flow of executing strategies with different broker allocations:
    1. Strategy Discovery with broker-aware queries
    2. Multi-Broker Execution Planning
    3. Parallel Broker Order Placement
    4. Cross-Broker Result Aggregation
    5. Multi-Broker Risk Management
    """
    
    def setUp(self):
        """Set up integration test environment with multi-broker scenarios"""
        super().setUp()
        
        # Initialize AWS test helper
        self.aws_helper = AWSTestHelper(self.aws_region)
        self.aws_helper.setup_eventbridge_mock()
        self.aws_helper.setup_stepfunctions_mock()
        
        # Create test basket for multi-broker testing
        self.test_basket_id = self.create_sample_basket("Multi-Broker Integration Test Basket")
        
        # Create complex multi-broker strategies
        self.setup_multi_broker_test_strategies()
        
    def setup_multi_broker_test_strategies(self):
        """Create strategies with complex multi-broker allocation scenarios"""
        
        # Strategy 1: Iron Condor with leg-specific broker allocation
        self.leg_specific_strategy_id = self.create_iron_condor_strategy(
            strategy_name="Leg-Specific Multi-Broker Iron Condor",
            underlying="NIFTY",
            entry_time="09:30",
            entry_days=['MONDAY']
        )
        
        # Allocate different legs to different brokers
        self.add_broker_allocation_to_strategy(
            strategy_id=self.leg_specific_strategy_id,
            broker_name="zerodha",
            lots_allocation=3,
            leg_numbers=[1, 2]  # Call spread on Zerodha
        )
        
        self.add_broker_allocation_to_strategy(
            strategy_id=self.leg_specific_strategy_id,
            broker_name="angel_one",
            lots_allocation=2,
            leg_numbers=[3, 4]  # Put spread on Angel One
        )
        
        # Strategy 2: Bull Call Spread with same legs across multiple brokers
        self.multi_broker_same_legs_strategy_id = self.create_bull_call_spread_strategy(
            strategy_name="Multi-Broker Bull Call Spread",
            underlying="BANKNIFTY",
            entry_time="10:00",
            entry_days=['TUESDAY']
        )
        
        # Same legs across different brokers for diversification
        self.add_broker_allocation_to_strategy(
            strategy_id=self.multi_broker_same_legs_strategy_id,
            broker_name="zerodha",
            lots_allocation=4,
            leg_numbers=[1, 2]  # Both legs on Zerodha
        )
        
        self.add_broker_allocation_to_strategy(
            strategy_id=self.multi_broker_same_legs_strategy_id,
            broker_name="finvasia",
            lots_allocation=6,
            leg_numbers=[1, 2]  # Both legs on Finvasia
        )
        
        # Strategy 3: Complex three-broker allocation
        self.three_broker_strategy_id = self.create_iron_condor_strategy(
            strategy_name="Three-Broker Iron Condor",
            underlying="FINNIFTY",
            entry_time="11:15",
            entry_days=['WEDNESDAY']
        )
        
        # Distribute across three brokers
        self.add_broker_allocation_to_strategy(
            strategy_id=self.three_broker_strategy_id,
            broker_name="zerodha",
            lots_allocation=2,
            leg_numbers=[1, 2]
        )
        
        self.add_broker_allocation_to_strategy(
            strategy_id=self.three_broker_strategy_id,
            broker_name="angel_one",
            lots_allocation=3,
            leg_numbers=[3]
        )
        
        self.add_broker_allocation_to_strategy(
            strategy_id=self.three_broker_strategy_id,
            broker_name="finvasia",
            lots_allocation=1,
            leg_numbers=[4]
        )
        
    def test_multi_broker_strategy_discovery_includes_allocation_data(self):
        """Test that strategy discovery includes broker allocation data for execution"""
        
        # Simulate strategy discovery for Monday 9:30 AM
        discovery_event = self.aws_helper.create_schedule_strategy_trigger_event(
            discovery_window_start='2025-09-01T09:25:00.000000+05:30',  # Monday 9:25 AM
            discovery_window_end='2025-09-01T09:30:00.000000+05:30',    # Monday 9:30 AM
            market_phase='MARKET_OPEN'
        )
        
        # Simulate discovery process with broker allocation enrichment
        discovered_strategies = self.simulate_multi_broker_strategy_discovery(discovery_event)
        
        # Should find the leg-specific strategy
        leg_specific_found = any(
            s['strategy_id'] == self.leg_specific_strategy_id 
            for s in discovered_strategies
        )
        self.assertTrue(leg_specific_found, "Leg-specific multi-broker strategy should be discovered")
        
        # Verify broker allocation data is included
        leg_specific_strategy = next(
            s for s in discovered_strategies 
            if s['strategy_id'] == self.leg_specific_strategy_id
        )
        
        self.assertIn('broker_allocations', leg_specific_strategy,
                     "Discovered strategy should include broker allocation data")
        
        allocations = leg_specific_strategy['broker_allocations']
        self.assertEqual(len(allocations), 2, "Should have allocations for 2 brokers")
        
        # Verify broker allocation details
        broker_names = {alloc['broker_name'] for alloc in allocations}
        self.assertEqual(broker_names, {'zerodha', 'angel_one'})
        
    def test_multi_broker_execution_planning_generates_broker_specific_orders(self):
        """Test that execution planning generates separate orders for each broker"""
        
        # Get strategy with broker allocations
        strategy_data = {
            'strategy_id': self.leg_specific_strategy_id,
            'strategy_name': 'Leg-Specific Multi-Broker Iron Condor',
            'underlying': 'NIFTY',
            'broker_allocations': self.get_strategy_broker_allocations(self.leg_specific_strategy_id),
            'legs': self.get_strategy_legs(self.leg_specific_strategy_id)
        }
        
        # Simulate execution planning
        execution_plan = self.simulate_multi_broker_execution_planning(strategy_data)
        
        # Should generate separate broker execution plans
        self.assertIn('broker_execution_plans', execution_plan)
        broker_plans = execution_plan['broker_execution_plans']
        
        self.assertEqual(len(broker_plans), 2, "Should have execution plans for 2 brokers")
        
        # Verify Zerodha execution plan
        zerodha_plan = next(p for p in broker_plans if p['broker_name'] == 'zerodha')
        self.assertEqual(len(zerodha_plan['orders']), 2, "Zerodha should have 2 orders (legs 1,2)")
        self.assertEqual(zerodha_plan['total_lots'], 3)
        
        # Verify Angel One execution plan
        angel_plan = next(p for p in broker_plans if p['broker_name'] == 'angel_one')
        self.assertEqual(len(angel_plan['orders']), 2, "Angel One should have 2 orders (legs 3,4)")
        self.assertEqual(angel_plan['total_lots'], 2)
        
        # Verify no overlap in leg assignments
        zerodha_legs = {order['leg_number'] for order in zerodha_plan['orders']}
        angel_legs = {order['leg_number'] for order in angel_plan['orders']}
        
        self.assertEqual(zerodha_legs.intersection(angel_legs), set(),
                        "No leg should be assigned to multiple brokers")
                        
    def test_parallel_broker_order_execution_simulation(self):
        """Test parallel execution of orders across multiple brokers"""
        
        # Create execution event with multi-broker strategy
        strategies = [{
            'strategy_id': self.multi_broker_same_legs_strategy_id,
            'strategy_name': 'Multi-Broker Bull Call Spread',
            'underlying': 'BANKNIFTY',
            'broker_allocations': self.get_strategy_broker_allocations(self.multi_broker_same_legs_strategy_id),
            'legs': self.get_strategy_legs(self.multi_broker_same_legs_strategy_id)
        }]
        
        execution_event = self.aws_helper.create_strategy_execution_event(
            strategies=strategies,
            execution_time='10:00',
            wait_seconds=30,
            market_phase='ACTIVE_TRADING'
        )
        
        # Simulate parallel broker execution
        execution_results = self.simulate_parallel_broker_execution(execution_event)
        
        # Verify results for each broker
        self.assertEqual(len(execution_results['broker_results']), 2,
                        "Should have results for 2 brokers")
        
        # Verify Zerodha execution result
        zerodha_result = next(r for r in execution_results['broker_results'] 
                             if r['broker_name'] == 'zerodha')
        
        self.assertEqual(zerodha_result['status'], 'SUCCESS')
        self.assertEqual(zerodha_result['orders_placed'], 2)  # Both legs
        self.assertEqual(zerodha_result['total_lots_executed'], 4)
        
        # Verify Finvasia execution result
        finvasia_result = next(r for r in execution_results['broker_results'] 
                              if r['broker_name'] == 'finvasia')
        
        self.assertEqual(finvasia_result['status'], 'SUCCESS')
        self.assertEqual(finvasia_result['orders_placed'], 2)  # Both legs
        self.assertEqual(finvasia_result['total_lots_executed'], 6)
        
        # Verify overall execution metrics
        self.assertEqual(execution_results['total_strategies_processed'], 1)
        self.assertEqual(execution_results['total_brokers_used'], 2)
        self.assertEqual(execution_results['total_lots_executed'], 10)  # 4 + 6
        
    def test_cross_broker_result_aggregation_and_reporting(self):
        """Test aggregation of results across multiple brokers for unified reporting"""
        
        # Simulate execution results from multiple brokers
        broker_results = [
            {
                'broker_name': 'zerodha',
                'strategy_id': self.three_broker_strategy_id,
                'orders_placed': 2,
                'orders_successful': 2,
                'orders_failed': 0,
                'total_lots_executed': 2,
                'execution_time': '11:15:23',
                'avg_fill_price': 125.50
            },
            {
                'broker_name': 'angel_one', 
                'strategy_id': self.three_broker_strategy_id,
                'orders_placed': 1,
                'orders_successful': 1,
                'orders_failed': 0,
                'total_lots_executed': 3,
                'execution_time': '11:15:27',
                'avg_fill_price': 67.25
            },
            {
                'broker_name': 'finvasia',
                'strategy_id': self.three_broker_strategy_id,
                'orders_placed': 1,
                'orders_successful': 0,
                'orders_failed': 1,  # Simulate failure
                'total_lots_executed': 0,
                'execution_time': None,
                'avg_fill_price': None,
                'error': 'Insufficient margin'
            }
        ]
        
        # Aggregate results across brokers
        aggregated_result = self.aggregate_multi_broker_results(
            self.three_broker_strategy_id, 
            broker_results
        )
        
        # Verify aggregated metrics
        self.assertEqual(aggregated_result['strategy_id'], self.three_broker_strategy_id)
        self.assertEqual(aggregated_result['total_brokers_attempted'], 3)
        self.assertEqual(aggregated_result['successful_brokers'], 2)
        self.assertEqual(aggregated_result['failed_brokers'], 1)
        
        # Verify order aggregation
        self.assertEqual(aggregated_result['total_orders_placed'], 4)
        self.assertEqual(aggregated_result['total_orders_successful'], 3)
        self.assertEqual(aggregated_result['total_orders_failed'], 1)
        
        # Verify lot aggregation
        self.assertEqual(aggregated_result['total_lots_executed'], 5)  # 2 + 3 + 0
        self.assertEqual(aggregated_result['planned_lots'], 6)  # 2 + 3 + 1
        
        # Verify partial execution status
        self.assertEqual(aggregated_result['execution_status'], 'PARTIAL_SUCCESS')
        self.assertIn('finvasia', aggregated_result['failed_brokers_details'])
        
    def test_multi_broker_risk_management_and_position_monitoring(self):
        """Test risk management across multiple brokers for unified position tracking"""
        
        # Simulate positions across multiple brokers for same strategy
        multi_broker_positions = [
            {
                'broker_name': 'zerodha',
                'strategy_id': self.leg_specific_strategy_id,
                'positions': [
                    {'leg_number': 1, 'quantity': 75, 'avg_price': 120.50, 'current_price': 115.25, 'pnl': -393.75},
                    {'leg_number': 2, 'quantity': -75, 'avg_price': 45.25, 'current_price': 48.75, 'pnl': -262.50}
                ]
            },
            {
                'broker_name': 'angel_one',
                'strategy_id': self.leg_specific_strategy_id,
                'positions': [
                    {'leg_number': 3, 'quantity': -50, 'avg_price': 78.50, 'current_price': 72.25, 'pnl': 312.50},
                    {'leg_number': 4, 'quantity': 50, 'avg_price': 25.75, 'current_price': 29.50, 'pnl': 187.50}
                ]
            }
        ]
        
        # Calculate unified risk metrics
        unified_risk = self.calculate_unified_risk_metrics(
            self.leg_specific_strategy_id,
            multi_broker_positions
        )
        
        # Verify unified position calculation
        self.assertEqual(unified_risk['total_brokers'], 2)
        self.assertEqual(unified_risk['net_pnl'], -156.25)  # -393.75 - 262.50 + 312.50 + 187.50
        
        # Verify risk metrics
        self.assertIn('max_loss_per_broker', unified_risk)
        self.assertIn('total_margin_used', unified_risk)
        self.assertIn('concentration_risk_by_broker', unified_risk)
        
        # Check if any broker has excessive risk
        zerodha_risk = unified_risk['broker_risk_breakdown']['zerodha']
        angel_risk = unified_risk['broker_risk_breakdown']['angel_one']
        
        self.assertLess(abs(zerodha_risk['pnl']), 10000, "Per-broker risk should be within limits")
        self.assertLess(abs(angel_risk['pnl']), 10000, "Per-broker risk should be within limits")
        
    def test_broker_failure_handling_and_fallback_execution(self):
        """Test handling of broker failures and fallback execution strategies"""
        
        # Simulate scenario where one broker fails
        execution_event = {
            'strategy_id': self.multi_broker_same_legs_strategy_id,
            'execution_time': '10:00',
            'broker_allocations': self.get_strategy_broker_allocations(self.multi_broker_same_legs_strategy_id)
        }
        
        # Simulate broker failure during execution
        execution_result = self.simulate_broker_failure_scenario(
            execution_event,
            failing_broker='zerodha',
            failure_type='CONNECTION_TIMEOUT'
        )
        
        # Verify failure is properly handled
        self.assertEqual(execution_result['overall_status'], 'PARTIAL_SUCCESS')
        self.assertEqual(execution_result['successful_brokers'], 1)
        self.assertEqual(execution_result['failed_brokers'], 1)
        
        # Verify successful broker executed its orders
        finvasia_result = execution_result['broker_results']['finvasia']
        self.assertEqual(finvasia_result['status'], 'SUCCESS')
        self.assertEqual(finvasia_result['orders_placed'], 2)
        
        # Verify failed broker is properly reported
        zerodha_result = execution_result['broker_results']['zerodha']
        self.assertEqual(zerodha_result['status'], 'FAILED')
        self.assertEqual(zerodha_result['error'], 'CONNECTION_TIMEOUT')
        
        # Verify fallback options are suggested
        self.assertIn('fallback_suggestions', execution_result)
        self.assertIn('retry_failed_broker', execution_result['fallback_suggestions'])
        
    def simulate_multi_broker_strategy_discovery(self, discovery_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate multi-broker aware strategy discovery"""
        
        # Use base discovery simulation but enrich with broker allocations
        discovered_strategies = self.simulate_strategy_discovery(discovery_event)
        
        # Enrich each strategy with broker allocation data
        for strategy in discovered_strategies:
            strategy_id = strategy['strategy_id']
            broker_allocations = self.get_strategy_broker_allocations(strategy_id)
            strategy['broker_allocations'] = broker_allocations
            
        return discovered_strategies
        
    def simulate_multi_broker_execution_planning(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate execution planning for multi-broker strategy"""
        
        broker_allocations = strategy_data['broker_allocations']
        strategy_legs = strategy_data['legs']
        
        broker_execution_plans = []
        
        for allocation in broker_allocations:
            broker_name = allocation['broker_name']
            lots_allocation = allocation['lots_allocation']
            leg_numbers = allocation['leg_numbers']
            
            # Create orders for allocated legs
            orders = []
            for leg_number in leg_numbers:
                leg = next(leg for leg in strategy_legs if leg['leg_number'] == leg_number)
                
                order = {
                    'leg_number': leg_number,
                    'symbol': leg['symbol'],
                    'strike_price': leg['strike_price'],
                    'option_type': leg['option_type'],
                    'quantity': lots_allocation * leg['lot_size'],
                    'order_type': 'MARKET',  # Simplified for testing
                    'expected_price': leg.get('premium', 100.0)  # Default premium
                }
                orders.append(order)
                
            broker_plan = {
                'broker_name': broker_name,
                'total_lots': lots_allocation,
                'orders': orders,
                'estimated_margin': lots_allocation * 50000  # Simplified calculation
            }
            broker_execution_plans.append(broker_plan)
            
        return {
            'strategy_id': strategy_data['strategy_id'],
            'broker_execution_plans': broker_execution_plans,
            'total_brokers': len(broker_execution_plans)
        }
        
    def simulate_parallel_broker_execution(self, execution_event: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate parallel execution across multiple brokers"""
        
        strategies = execution_event['strategies']
        all_broker_results = []
        
        for strategy in strategies:
            strategy_id = strategy['strategy_id']
            broker_allocations = strategy['broker_allocations']
            
            for allocation in broker_allocations:
                broker_name = allocation['broker_name']
                lots_allocation = allocation['lots_allocation']
                leg_count = len(allocation['leg_numbers'])
                
                # Simulate broker execution (simplified)
                broker_result = {
                    'broker_name': broker_name,
                    'strategy_id': strategy_id,
                    'status': 'SUCCESS',
                    'orders_placed': leg_count,
                    'orders_successful': leg_count,
                    'orders_failed': 0,
                    'total_lots_executed': lots_allocation,
                    'execution_time': '10:00:15',  # Simulated
                    'avg_execution_price': 95.25
                }
                all_broker_results.append(broker_result)
                
        return {
            'broker_results': all_broker_results,
            'total_strategies_processed': len(strategies),
            'total_brokers_used': len(all_broker_results),
            'total_lots_executed': sum(r['total_lots_executed'] for r in all_broker_results)
        }
        
    def aggregate_multi_broker_results(self, strategy_id: str, broker_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results across multiple brokers for unified reporting"""
        
        successful_brokers = sum(1 for r in broker_results if r['orders_successful'] > 0)
        failed_brokers = len(broker_results) - successful_brokers
        
        total_orders_placed = sum(r['orders_placed'] for r in broker_results)
        total_orders_successful = sum(r['orders_successful'] for r in broker_results)
        total_orders_failed = sum(r['orders_failed'] for r in broker_results)
        total_lots_executed = sum(r['total_lots_executed'] for r in broker_results)
        
        # Determine execution status
        if failed_brokers == 0:
            execution_status = 'SUCCESS'
        elif successful_brokers == 0:
            execution_status = 'FAILED'
        else:
            execution_status = 'PARTIAL_SUCCESS'
            
        failed_brokers_details = {
            r['broker_name']: r.get('error', 'Unknown error')
            for r in broker_results if r['orders_successful'] == 0
        }
        
        return {
            'strategy_id': strategy_id,
            'execution_status': execution_status,
            'total_brokers_attempted': len(broker_results),
            'successful_brokers': successful_brokers,
            'failed_brokers': failed_brokers,
            'total_orders_placed': total_orders_placed,
            'total_orders_successful': total_orders_successful,
            'total_orders_failed': total_orders_failed,
            'total_lots_executed': total_lots_executed,
            'planned_lots': sum(r.get('planned_lots', r['total_lots_executed']) for r in broker_results),
            'failed_brokers_details': failed_brokers_details
        }
        
    def calculate_unified_risk_metrics(self, strategy_id: str, multi_broker_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate unified risk metrics across multiple brokers"""
        
        total_pnl = 0
        broker_risk_breakdown = {}
        
        for broker_position in multi_broker_positions:
            broker_name = broker_position['broker_name']
            positions = broker_position['positions']
            
            broker_pnl = sum(pos['pnl'] for pos in positions)
            total_pnl += broker_pnl
            
            broker_risk_breakdown[broker_name] = {
                'pnl': broker_pnl,
                'position_count': len(positions),
                'net_quantity': sum(pos['quantity'] for pos in positions)
            }
            
        return {
            'strategy_id': strategy_id,
            'total_brokers': len(multi_broker_positions),
            'net_pnl': total_pnl,
            'broker_risk_breakdown': broker_risk_breakdown,
            'max_loss_per_broker': max(abs(b['pnl']) for b in broker_risk_breakdown.values()),
            'total_margin_used': 150000,  # Simplified calculation
            'concentration_risk_by_broker': {
                broker: abs(risk['pnl']) / abs(total_pnl) if total_pnl != 0 else 0
                for broker, risk in broker_risk_breakdown.items()
            }
        }
        
    def simulate_broker_failure_scenario(self, execution_event: Dict[str, Any], 
                                       failing_broker: str, failure_type: str) -> Dict[str, Any]:
        """Simulate broker failure scenario and fallback handling"""
        
        broker_allocations = execution_event['broker_allocations']
        broker_results = {}
        
        for allocation in broker_allocations:
            broker_name = allocation['broker_name']
            
            if broker_name == failing_broker:
                # Simulate failure
                broker_results[broker_name] = {
                    'status': 'FAILED',
                    'error': failure_type,
                    'orders_placed': 0,
                    'orders_successful': 0,
                    'total_lots_executed': 0
                }
            else:
                # Simulate success
                broker_results[broker_name] = {
                    'status': 'SUCCESS',
                    'orders_placed': len(allocation['leg_numbers']),
                    'orders_successful': len(allocation['leg_numbers']),
                    'total_lots_executed': allocation['lots_allocation']
                }
                
        successful_brokers = sum(1 for r in broker_results.values() if r['status'] == 'SUCCESS')
        failed_brokers = len(broker_results) - successful_brokers
        
        return {
            'overall_status': 'PARTIAL_SUCCESS' if successful_brokers > 0 and failed_brokers > 0 else 
                             'SUCCESS' if failed_brokers == 0 else 'FAILED',
            'successful_brokers': successful_brokers,
            'failed_brokers': failed_brokers,
            'broker_results': broker_results,
            'fallback_suggestions': [
                'retry_failed_broker',
                'redistribute_to_successful_brokers',
                'manual_intervention_required'
            ]
        }


if __name__ == '__main__':
    unittest.main()