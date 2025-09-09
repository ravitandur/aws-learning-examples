import unittest
import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'fixtures'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared', 'fixtures'))

from OptionsStrategyTestBase import OptionsStrategyTestBase


class TestSimpleBasketAllocation(OptionsStrategyTestBase):
    """
    Simple test to validate basket-level broker allocation infrastructure
    """
    
    def test_basket_allocation_basic_functionality(self):
        """Test basic basket allocation functionality"""
        
        # Create test basket
        test_basket_id = self.create_sample_basket("Test Basket")
        
        # Add broker allocation
        allocation_id = self.add_broker_allocation_to_basket(
            basket_id=test_basket_id,
            broker_name="zerodha",
            client_id="test_client_001",
            lot_multiplier=5,
            priority=1
        )
        
        # Verify allocation was created
        self.assertIsNotNone(allocation_id)
        
        # Query allocations using GSI
        allocations = self.get_basket_broker_allocations(test_basket_id)
        
        # Verify results
        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations[0]['broker_name'], 'zerodha')
        self.assertEqual(allocations[0]['lot_multiplier'], 5)
        
        # Test total calculation
        total_lots = self.calculate_total_lots_for_basket(test_basket_id)
        self.assertEqual(total_lots, 5)
        
        print("✅ Basket allocation basic functionality test passed!")


if __name__ == '__main__':
    unittest.main()