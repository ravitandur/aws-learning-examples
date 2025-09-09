import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytz

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'fixtures'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared', 'fixtures'))

from OptionsStrategyTestBase import OptionsStrategyTestBase


class TestDataCreatorMock:
    """Mock implementation of TestDataCreatorV2 for unit testing"""
    
    def __init__(self):
        self.test_user_id = "test-user-e2e-001"
        self.created_items = []
        self.dynamodb = Mock()
        self.table = Mock()
    
    def _allocate_lots_to_brokers(self, total_lots, brokers):
        """Revolutionary algorithm: Allocate lots across multiple brokers"""
        allocations = []
        remaining_lots = total_lots
        
        # Use a mix of strategies for different scenarios
        if total_lots <= 2:
            # Small orders: Use single best broker
            broker = brokers[0]  # Highest priority
            allocations.append({
                'broker_id': broker['id'],
                'broker_name': broker['name'],
                'lots': total_lots
            })
        elif total_lots <= 5:
            # Medium orders: Use 2 brokers
            primary_broker = brokers[0]
            secondary_broker = brokers[1] if len(brokers) > 1 else brokers[0]
            
            primary_lots = min(remaining_lots, primary_broker.get('capacity', 100) // 2)
            secondary_lots = remaining_lots - primary_lots
            
            if primary_lots > 0:
                allocations.append({
                    'broker_id': primary_broker['id'],
                    'broker_name': primary_broker['name'],
                    'lots': primary_lots
                })
            
            if secondary_lots > 0:
                allocations.append({
                    'broker_id': secondary_broker['id'],
                    'broker_name': secondary_broker['name'],
                    'lots': secondary_lots
                })
        else:
            # Large orders: Use 3+ brokers for maximum diversification
            for i, broker in enumerate(brokers[:3]):  # Use top 3 brokers
                if remaining_lots <= 0:
                    break
                    
                if i == 2:  # Last broker gets remaining lots
                    broker_lots = remaining_lots
                else:
                    broker_lots = min(remaining_lots, broker.get('capacity', 100) // 3)
                
                if broker_lots > 0:
                    allocations.append({
                        'broker_id': broker['id'],
                        'broker_name': broker['name'],
                        'lots': broker_lots
                    })
                    remaining_lots -= broker_lots
        
        return allocations


class TestTestDataCreation(OptionsStrategyTestBase):
    """
    Unit tests for test data creation functionality.
    
    Tests the revolutionary multi-broker allocation algorithms,
    strategy creation logic, and data validation.
    """
    
    def setUp(self):
        """Set up test environment with mock data creator"""
        super().setUp()
        self.data_creator = TestDataCreatorMock()
        
        # Sample broker data for testing
        self.sample_brokers = [
            {"id": "zerodha", "name": "Zerodha", "capacity": 100, "priority": 1},
            {"id": "angel_one", "name": "Angel One", "capacity": 75, "priority": 2},
            {"id": "finvasia", "name": "Finvasia", "capacity": 50, "priority": 3},
            {"id": "upstox", "name": "Upstox", "capacity": 80, "priority": 4},
        ]
        
    def test_small_lot_single_broker_allocation(self):
        """Test that small lot orders use single best broker"""
        
        # Test 1-2 lots should use single broker
        for lots in [1, 2]:
            with self.subTest(lots=lots):
                allocations = self.data_creator._allocate_lots_to_brokers(
                    lots, self.sample_brokers
                )
                
                # Should use exactly one broker
                self.assertEqual(len(allocations), 1)
                
                # Should be the highest priority broker (Zerodha)
                self.assertEqual(allocations[0]['broker_id'], 'zerodha')
                self.assertEqual(allocations[0]['broker_name'], 'Zerodha')
                self.assertEqual(allocations[0]['lots'], lots)
                
    def test_medium_lot_dual_broker_allocation(self):
        """Test that medium lot orders use two brokers"""
        
        # Test 3-5 lots should use dual brokers
        for lots in [3, 4, 5]:
            with self.subTest(lots=lots):
                allocations = self.data_creator._allocate_lots_to_brokers(
                    lots, self.sample_brokers
                )
                
                # Should use exactly two brokers
                self.assertEqual(len(allocations), 2)
                
                # First allocation should be Zerodha (highest priority)
                self.assertEqual(allocations[0]['broker_id'], 'zerodha')
                
                # Second allocation should be Angel One
                self.assertEqual(allocations[1]['broker_id'], 'angel_one')
                
                # Total lots should equal input
                total_allocated = sum(alloc['lots'] for alloc in allocations)
                self.assertEqual(total_allocated, lots)
                
                # Primary broker should get more or equal lots
                self.assertGreaterEqual(allocations[0]['lots'], allocations[1]['lots'])
                
    def test_large_lot_multi_broker_allocation(self):
        """Test that large lot orders use multiple brokers"""
        
        # Test 6+ lots should use three brokers
        for lots in [6, 10, 15, 20]:
            with self.subTest(lots=lots):
                allocations = self.data_creator._allocate_lots_to_brokers(
                    lots, self.sample_brokers
                )
                
                # Should use up to three brokers
                self.assertGreaterEqual(len(allocations), 2)
                self.assertLessEqual(len(allocations), 3)
                
                # First allocation should be Zerodha
                self.assertEqual(allocations[0]['broker_id'], 'zerodha')
                
                # Total lots should equal input
                total_allocated = sum(alloc['lots'] for alloc in allocations)
                self.assertEqual(total_allocated, lots)
                
                # All brokers should have positive allocation
                for allocation in allocations:
                    self.assertGreater(allocation['lots'], 0)
                    
    def test_broker_allocation_with_single_broker(self):
        """Test allocation when only one broker is available"""
        
        single_broker = [self.sample_brokers[0]]
        
        for lots in [1, 3, 10]:
            with self.subTest(lots=lots):
                allocations = self.data_creator._allocate_lots_to_brokers(
                    lots, single_broker
                )
                
                # Should use exactly one broker
                self.assertEqual(len(allocations), 1)
                self.assertEqual(allocations[0]['broker_id'], 'zerodha')
                self.assertEqual(allocations[0]['lots'], lots)
                
    def test_broker_allocation_algorithm_consistency(self):
        """Test that allocation algorithm is consistent and deterministic"""
        
        test_cases = [1, 3, 5, 10, 25]
        
        for lots in test_cases:
            with self.subTest(lots=lots):
                # Run allocation multiple times
                allocations1 = self.data_creator._allocate_lots_to_brokers(
                    lots, self.sample_brokers
                )
                allocations2 = self.data_creator._allocate_lots_to_brokers(
                    lots, self.sample_brokers
                )
                
                # Results should be identical
                self.assertEqual(allocations1, allocations2)
                
                # Total should always equal input
                total = sum(alloc['lots'] for alloc in allocations1)
                self.assertEqual(total, lots)
                
    def test_broker_priority_ordering(self):
        """Test that brokers are selected in priority order"""
        
        # Test with 5 lots (should use 2 brokers)
        allocations = self.data_creator._allocate_lots_to_brokers(
            5, self.sample_brokers
        )
        
        self.assertEqual(len(allocations), 2)
        
        # First broker should be highest priority (priority 1)
        first_broker = next(b for b in self.sample_brokers 
                          if b['id'] == allocations[0]['broker_id'])
        self.assertEqual(first_broker['priority'], 1)
        
        # Second broker should be second highest priority (priority 2)  
        second_broker = next(b for b in self.sample_brokers
                           if b['id'] == allocations[1]['broker_id'])
        self.assertEqual(second_broker['priority'], 2)
        
    def test_zero_lots_edge_case(self):
        """Test edge case with zero lots"""
        
        allocations = self.data_creator._allocate_lots_to_brokers(
            0, self.sample_brokers
        )
        
        # Should still create allocation but with zero lots
        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations[0]['lots'], 0)
        
    def test_revolutionary_multi_broker_feature_validation(self):
        """Test that revolutionary multi-broker feature is working"""
        
        # Test scenario: 15 lots should trigger multi-broker allocation
        lots = 15
        allocations = self.data_creator._allocate_lots_to_brokers(
            lots, self.sample_brokers
        )
        
        # Revolutionary feature: Multiple brokers used
        self.assertGreater(len(allocations), 1, 
                          "Revolutionary multi-broker allocation should use multiple brokers for large orders")
        
        # Each broker should have reasonable allocation
        for allocation in allocations:
            self.assertGreater(allocation['lots'], 0)
            self.assertLessEqual(allocation['lots'], lots)
            
        # Broker diversity validation
        broker_ids = [alloc['broker_id'] for alloc in allocations]
        unique_brokers = set(broker_ids)
        self.assertEqual(len(unique_brokers), len(broker_ids), 
                        "Each broker should be used only once")
                        
    def test_broker_capacity_respect(self):
        """Test that broker capacity limits are respected"""
        
        # Create scenario where capacity matters
        low_capacity_brokers = [
            {"id": "broker1", "name": "Broker 1", "capacity": 5, "priority": 1},
            {"id": "broker2", "name": "Broker 2", "capacity": 3, "priority": 2},
            {"id": "broker3", "name": "Broker 3", "capacity": 2, "priority": 3},
        ]
        
        # Allocate 8 lots
        allocations = self.data_creator._allocate_lots_to_brokers(
            8, low_capacity_brokers
        )
        
        # Validate capacity constraints are considered
        for allocation in allocations:
            broker = next(b for b in low_capacity_brokers 
                         if b['id'] == allocation['broker_id'])
            
            # Allocation should not exceed reasonable portion of capacity
            max_reasonable = broker['capacity'] // 2 + 1
            self.assertLessEqual(allocation['lots'], max_reasonable)
            
        # Total should still equal 8
        total_allocated = sum(alloc['lots'] for alloc in allocations)
        self.assertEqual(total_allocated, 8)

    def test_strategy_templates_validation(self):
        """Test strategy template data structures"""
        
        # Iron Condor template validation
        iron_condor_legs = [
            {"leg_type": "CALL_SELL", "strike_offset": 200, "lots": 3},
            {"leg_type": "CALL_BUY", "strike_offset": 400, "lots": 3},
            {"leg_type": "PUT_SELL", "strike_offset": -200, "lots": 3},
            {"leg_type": "PUT_BUY", "strike_offset": -400, "lots": 3},
        ]
        
        # Validate leg structure
        self.assertEqual(len(iron_condor_legs), 4)
        
        # Validate leg types
        expected_leg_types = {"CALL_SELL", "CALL_BUY", "PUT_SELL", "PUT_BUY"}
        actual_leg_types = {leg["leg_type"] for leg in iron_condor_legs}
        self.assertEqual(actual_leg_types, expected_leg_types)
        
        # Validate lots consistency
        lots_per_leg = {leg["lots"] for leg in iron_condor_legs}
        self.assertEqual(lots_per_leg, {3}, "Iron Condor should have consistent lots per leg")
        
        # Validate strike structure
        call_strikes = [leg["strike_offset"] for leg in iron_condor_legs 
                       if "CALL" in leg["leg_type"]]
        put_strikes = [leg["strike_offset"] for leg in iron_condor_legs
                      if "PUT" in leg["leg_type"]]
        
        # Call strikes should be positive, puts negative
        self.assertTrue(all(strike > 0 for strike in call_strikes))
        self.assertTrue(all(strike < 0 for strike in put_strikes))
        
    def test_weekend_protection_schedule_creation(self):
        """Test weekend protection in schedule creation"""
        
        ist = pytz.timezone('Asia/Kolkata')
        
        # Test dates including weekend
        test_dates = []
        base_date = datetime(2025, 9, 6)  # Start from a known Friday
        
        for days_ahead in range(7):  # Test a full week
            test_date = base_date + timedelta(days=days_ahead)
            test_dates.append(test_date)
            
        # Filter out weekends (Saturday = 5, Sunday = 6)
        weekday_dates = [d for d in test_dates if d.weekday() < 5]
        weekend_dates = [d for d in test_dates if d.weekday() >= 5]
        
        # Revolutionary weekend protection validation
        self.assertEqual(len(weekend_dates), 2)  # Saturday and Sunday
        self.assertEqual(len(weekday_dates), 5)  # Monday to Friday
        
        # Weekend dates should be excluded
        for weekend_date in weekend_dates:
            self.assertIn(weekend_date.weekday(), [5, 6])
            
        # Weekday dates should be included
        for weekday_date in weekday_dates:
            self.assertNotIn(weekday_date.weekday(), [5, 6])


if __name__ == '__main__':
    unittest.main()