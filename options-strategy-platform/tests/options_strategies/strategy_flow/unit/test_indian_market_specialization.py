import unittest
import sys
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'fixtures'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared', 'fixtures'))

from OptionsStrategyTestBase import OptionsStrategyTestBase


class TestIndianMarketSpecialization(OptionsStrategyTestBase):
    """
    Test Indian market specialization features including:
    - Index-specific lot sizes (NIFTY, BANKNIFTY, FINNIFTY, etc.)
    - Expiry handling (weekly/monthly expiries)
    - Market timing (9:15-15:30 IST)
    - Holiday calendar integration
    """
    
    def setUp(self):
        """Set up test environment with Indian market scenarios"""
        super().setUp()
        
        # Create sample basket for Indian market testing
        self.test_basket_id = self.create_sample_basket("Indian Market Test Basket")
        
    def test_nifty_index_lot_size_and_expiry_handling(self):
        """Test NIFTY index with correct lot size and Thursday expiry"""
        
        # Create NIFTY Iron Condor strategy
        nifty_strategy_id = self.create_iron_condor_strategy(
            strategy_name="NIFTY Weekly Iron Condor",
            underlying="NIFTY",
            entry_time="09:30",
            entry_days=['MONDAY', 'TUESDAY', 'WEDNESDAY']
        )
        
        # Verify strategy was created successfully
        strategy = self.get_strategy_details(nifty_strategy_id)
        
        # Verify NIFTY-specific properties
        self.assertEqual(strategy['underlying'], 'NIFTY')
        self.assertEqual(strategy['lot_size'], 25, "NIFTY lot size should be 25")
        
        # Verify Iron Condor legs for NIFTY
        strategy_details = self.get_strategy_details(nifty_strategy_id)
        legs = strategy_details['legs']
        self.assertEqual(len(legs), 4, "Iron Condor should have 4 legs")
        
        # All legs should have NIFTY as underlying
        for leg in legs:
            self.assertEqual(leg['underlying'], 'NIFTY')
            self.assertEqual(leg['lot_size'], 25)
            
        # Verify expiry calculation (should be Thursday)
        for leg in legs:
            expiry_date = datetime.strptime(leg['expiry_date'], '%Y-%m-%d')
            self.assertEqual(expiry_date.weekday(), 3, "NIFTY expiry should be Thursday (weekday 3)")
            
    def test_banknifty_index_lot_size_and_expiry_handling(self):
        """Test BANKNIFTY index with correct lot size and Wednesday expiry"""
        
        # Create BANKNIFTY Bull Call Spread strategy
        banknifty_strategy_id = self.create_bull_call_spread_strategy(
            strategy_name="BANKNIFTY Bull Call Spread",
            underlying="BANKNIFTY",
            entry_time="10:00"
        )
        
        # Verify strategy was created successfully
        strategy = self.get_strategy_details(banknifty_strategy_id)
        
        # Verify BANKNIFTY-specific properties
        self.assertEqual(strategy['underlying'], 'BANKNIFTY')
        self.assertEqual(strategy['lot_size'], 15, "BANKNIFTY lot size should be 15")
        
        # Verify Bull Call Spread legs for BANKNIFTY
        strategy_details = self.get_strategy_details(banknifty_strategy_id)
        legs = strategy_details['legs']
        self.assertEqual(len(legs), 2, "Bull Call Spread should have 2 legs")
        
        # All legs should have BANKNIFTY as underlying
        for leg in legs:
            self.assertEqual(leg['underlying'], 'BANKNIFTY')
            self.assertEqual(leg['lot_size'], 15)
            
        # Verify expiry calculation (should be Wednesday)
        for leg in legs:
            expiry_date = datetime.strptime(leg['expiry_date'], '%Y-%m-%d')
            self.assertEqual(expiry_date.weekday(), 2, "BANKNIFTY expiry should be Wednesday (weekday 2)")
            
    def test_all_indian_indices_lot_sizes_and_expiries(self):
        """Test all supported Indian indices with their specific lot sizes and expiry days"""
        
        indian_indices_config = [
            # (underlying, lot_size, expiry_weekday, expiry_day_name)
            ('NIFTY', 25, 3, 'Thursday'),
            ('BANKNIFTY', 15, 2, 'Wednesday'), 
            ('FINNIFTY', 25, 1, 'Tuesday'),
            ('MIDCPNIFTY', 75, 0, 'Monday'),
            ('SENSEX', 10, 4, 'Friday')
        ]
        
        for underlying, expected_lot_size, expected_expiry_weekday, expiry_day_name in indian_indices_config:
            
            # Create strategy for this underlying
            strategy_id = self.create_sample_strategy(
                strategy_name=f"{underlying} Test Strategy",
                underlying=underlying,
                entry_time="11:30"
            )
            
            # Verify strategy properties
            strategy = self.get_strategy_details(strategy_id)
            self.assertEqual(strategy['underlying'], underlying)
            self.assertEqual(strategy['lot_size'], expected_lot_size,
                           f"{underlying} lot size should be {expected_lot_size}")
            
            # Verify legs have correct properties
            strategy_details = self.get_strategy_details(strategy_id)
            legs = strategy_details['legs']
            for leg in legs:
                self.assertEqual(leg['underlying'], underlying)
                self.assertEqual(leg['lot_size'], expected_lot_size)
                
                # Verify expiry weekday
                expiry_date = datetime.strptime(leg['expiry_date'], '%Y-%m-%d')
                self.assertEqual(expiry_date.weekday(), expected_expiry_weekday,
                               f"{underlying} expiry should be {expiry_day_name} (weekday {expected_expiry_weekday})")
                               
    def test_indian_market_timing_validation(self):
        """Test validation of Indian market timing (9:15-15:30 IST)"""
        
        # Valid market timings
        valid_timings = [
            '09:15',  # Market open
            '09:30',  # Normal trading
            '12:00',  # Mid-day
            '15:00',  # Afternoon
            '15:30'   # Market close
        ]
        
        for timing in valid_timings:
            strategy_id = self.create_sample_strategy(
                strategy_name=f"Valid Timing Test {timing}",
                entry_time=timing,
                underlying="NIFTY"
            )
            
            strategy = self.get_strategy_details(strategy_id)
            self.assertEqual(strategy['entry_time'], timing,
                           f"Valid timing {timing} should be accepted")
                           
        # Invalid market timings (should be handled by business logic)
        invalid_timings = [
            '09:14',  # Before market open
            '15:31',  # After market close
            '03:00',  # Middle of night
            '20:00'   # Evening
        ]
        
        for timing in invalid_timings:
            # These should either fail validation or be flagged as non-market hours
            # Implementation depends on business requirements
            try:
                strategy_id = self.create_sample_strategy(
                    strategy_name=f"Invalid Timing Test {timing}",
                    entry_time=timing,
                    underlying="NIFTY"
                )
                # If allowed, should be marked as non-market hours
                strategy = self.get_strategy_details(strategy_id)
                # Add business logic validation here if needed
                
            except ValueError:
                # Expected for invalid timings
                pass
                
    def test_weekly_vs_monthly_expiry_calculation(self):
        """Test calculation of weekly vs monthly expiry dates"""
        
        # Create strategies to test expiry calculation
        nifty_strategy_id = self.create_sample_strategy(
            strategy_name="NIFTY Expiry Test",
            underlying="NIFTY",
            entry_time="10:00"
        )
        
        strategy_details = self.get_strategy_details(nifty_strategy_id)
        legs = strategy_details['legs']
        
        for leg in legs:
            expiry_date_str = leg['expiry_date']
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
            
            # Should be a Thursday (NIFTY expiry day)
            self.assertEqual(expiry_date.weekday(), 3, "NIFTY expiry should be Thursday")
            
            # Should be in the future from creation date
            creation_date = datetime.now().date()
            self.assertGreater(expiry_date.date(), creation_date,
                             "Expiry date should be in the future")
                             
            # Should be within reasonable range (1-30 days typically)
            days_to_expiry = (expiry_date.date() - creation_date).days
            self.assertGreater(days_to_expiry, 0, "Days to expiry should be positive")
            self.assertLessEqual(days_to_expiry, 35, "Days to expiry should be reasonable (<= 35 days)")
            
    def test_indian_market_holiday_awareness(self):
        """Test awareness of Indian market holidays"""
        
        # Test with known Indian market holidays (if holiday calendar is implemented)
        # This is a placeholder for holiday calendar integration
        
        # Create strategy and verify it doesn't execute on holidays
        strategy_id = self.create_sample_strategy(
            strategy_name="Holiday Test Strategy",
            entry_time="10:00",
            underlying="NIFTY"
        )
        
        # In a full implementation, this would check against holiday calendar
        # For now, verify basic functionality exists
        strategy = self.get_strategy_details(strategy_id)
        self.assertIsNotNone(strategy, "Strategy should be created successfully")
        
        # TODO: Add holiday calendar integration tests when implemented
        # - Test Republic Day (Jan 26)
        # - Test Independence Day (Aug 15)
        # - Test Diwali (variable date)
        # - Test other NSE holidays
        
    def test_options_chain_strike_price_calculation(self):
        """Test strike price calculation for Indian index options"""
        
        # Test NIFTY strike price intervals (typically 50 points)
        nifty_strategy_id = self.create_iron_condor_strategy(
            strategy_name="NIFTY Strike Price Test",
            underlying="NIFTY",
            entry_time="10:00"
        )
        
        nifty_strategy_details = self.get_strategy_details(nifty_strategy_id)
        legs = nifty_strategy_details['legs']
        
        # Verify strike prices are valid for NIFTY
        for leg in legs:
            strike_price = leg['strike_price']
            
            # NIFTY strikes should be multiples of 50
            self.assertEqual(strike_price % 50, 0,
                           f"NIFTY strike price {strike_price} should be multiple of 50")
            
            # Should be reasonable range (assuming NIFTY around 15000-25000)
            self.assertGreaterEqual(strike_price, 10000, "NIFTY strike should be reasonable minimum")
            self.assertLessEqual(strike_price, 30000, "NIFTY strike should be reasonable maximum")
            
        # Test BANKNIFTY strike price intervals (typically 100 points)
        banknifty_strategy_id = self.create_bull_call_spread_strategy(
            strategy_name="BANKNIFTY Strike Price Test",
            underlying="BANKNIFTY",
            entry_time="10:00"
        )
        
        banknifty_strategy_details = self.get_strategy_details(banknifty_strategy_id)
        banknifty_legs = banknifty_strategy_details['legs']
        
        for leg in banknifty_legs:
            strike_price = leg['strike_price']
            
            # BANKNIFTY strikes should be multiples of 100
            self.assertEqual(strike_price % 100, 0,
                           f"BANKNIFTY strike price {strike_price} should be multiple of 100")
                           
    def test_indian_rupee_currency_handling(self):
        """Test handling of Indian Rupee currency in premiums and calculations"""
        
        # Create strategy and verify currency handling
        strategy_id = self.create_sample_strategy(
            strategy_name="INR Currency Test",
            underlying="NIFTY",
            entry_time="11:00"
        )
        
        strategy_details = self.get_strategy_details(strategy_id)
        legs = strategy_details['legs']
        
        for leg in legs:
            # Verify premium is in reasonable INR range
            if 'premium' in leg:
                premium = leg['premium']
                
                # Options premiums in India typically range from 1 to 1000+ INR
                self.assertGreaterEqual(premium, 0.01, "Premium should be positive")
                self.assertLessEqual(premium, 5000, "Premium should be reasonable maximum")
                
            # Verify lot value calculation includes lot size
            lot_value = leg['strike_price'] * leg['lot_size']
            
            # Should be reasonable for Indian market
            self.assertGreater(lot_value, 10000, "Lot value should be significant for Indian options")
            
    def test_multi_index_strategy_comparison(self):
        """Test creating strategies across different Indian indices for comparison"""
        
        indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
        strategies = {}
        
        for index in indices:
            strategy_id = self.create_sample_strategy(
                strategy_name=f"{index} Comparison Strategy",
                underlying=index,
                entry_time="12:00"
            )
            strategies[index] = strategy_id
            
        # Compare properties across indices
        for index in indices:
            strategy = self.get_strategy_details(strategies[index])
            strategy_details = self.get_strategy_details(strategies[index])
            legs = strategy_details['legs']
            
            # Each should have appropriate lot size
            if index == 'NIFTY':
                self.assertEqual(strategy['lot_size'], 25)
            elif index == 'BANKNIFTY':
                self.assertEqual(strategy['lot_size'], 15) 
            elif index == 'FINNIFTY':
                self.assertEqual(strategy['lot_size'], 25)
                
            # Each should have appropriate expiry day
            for leg in legs:
                expiry_date = datetime.strptime(leg['expiry_date'], '%Y-%m-%d')
                if index == 'NIFTY':
                    self.assertEqual(expiry_date.weekday(), 3)  # Thursday
                elif index == 'BANKNIFTY':
                    self.assertEqual(expiry_date.weekday(), 2)  # Wednesday
                elif index == 'FINNIFTY':
                    self.assertEqual(expiry_date.weekday(), 1)  # Tuesday
                    
    def test_indian_market_volatility_and_iv_ranges(self):
        """Test Indian market specific volatility and implied volatility ranges"""
        
        # Create strategy for volatility testing
        strategy_id = self.create_iron_condor_strategy(
            strategy_name="IV Range Test Strategy",
            underlying="NIFTY",
            entry_time="11:00"
        )
        
        strategy_details = self.get_strategy_details(strategy_id)
        legs = strategy_details['legs']
        
        for leg in legs:
            # If IV is calculated, verify it's in reasonable range for Indian market
            if 'implied_volatility' in leg:
                iv = leg['implied_volatility']
                
                # Indian market IV typically ranges from 10% to 80%
                self.assertGreaterEqual(iv, 0.05, "IV should be at least 5%")
                self.assertLessEqual(iv, 1.50, "IV should be at most 150%")
                
            # Verify Greeks if calculated
            if 'delta' in leg:
                delta = abs(leg['delta'])
                self.assertLessEqual(delta, 1.0, "Delta should be <= 1.0")
                
            if 'gamma' in leg:
                gamma = leg['gamma']
                self.assertGreaterEqual(gamma, 0, "Gamma should be non-negative")
                
            if 'theta' in leg:
                theta = leg['theta']
                # Theta is typically negative (time decay)
                self.assertLessEqual(theta, 0, "Theta should be non-positive")


if __name__ == '__main__':
    unittest.main()