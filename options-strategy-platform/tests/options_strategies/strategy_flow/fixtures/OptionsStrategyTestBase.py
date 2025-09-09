import sys
import os
from decimal import Decimal
from typing import Dict, Any, List
from datetime import datetime, timezone

# Add paths for importing shared fixtures
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared', 'fixtures'))

from BaseStrategyTestCase import BaseStrategyTestCase


class OptionsStrategyTestBase(BaseStrategyTestCase):
    """
    Base test case specifically for options strategy testing.
    
    Extends BaseStrategyTestCase with options-specific utilities:
    - Options strategy templates (Iron Condor, Straddle, Strangle, etc.)
    - Indian market specialization (NIFTY, BANKNIFTY, FINNIFTY)
    - Options leg validation
    - Greeks calculation testing utilities
    - Expiry date handling
    """
    
    def setUp(self):
        """Set up options strategy specific test infrastructure"""
        super().setUp()
        
        # Options strategy specific configuration
        self.supported_underlyings = {
            'NIFTY': {'lot_size': 25, 'expiry_day': 'THURSDAY'},
            'BANKNIFTY': {'lot_size': 15, 'expiry_day': 'WEDNESDAY'}, 
            'FINNIFTY': {'lot_size': 25, 'expiry_day': 'TUESDAY'},
            'MIDCPNIFTY': {'lot_size': 75, 'expiry_day': 'MONDAY'},
            'SENSEX': {'lot_size': 10, 'expiry_day': 'FRIDAY'}
        }
        
        # Common strike prices for testing
        self.nifty_strikes = [19000, 19100, 19200, 19300, 19400, 19500, 19600, 19700, 19800, 19900, 20000]
        self.banknifty_strikes = [44000, 44500, 45000, 45500, 46000, 46500, 47000, 47500, 48000, 48500, 49000]
        
    def create_iron_condor_strategy(self,
                                  strategy_name: str = "Test Iron Condor",
                                  underlying: str = "NIFTY",
                                  entry_time: str = "09:30",
                                  exit_time: str = "15:20",
                                  entry_days: List[str] = None,
                                  atm_price: Decimal = Decimal('19500')) -> str:
        """Create an Iron Condor options strategy for testing"""
        
        if entry_days is None:
            entry_days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
            
        # Iron Condor: Sell Put Spread + Sell Call Spread
        # Structure: Buy Put (OTM) + Sell Put (ITM) + Sell Call (ITM) + Buy Call (OTM)
        legs = [
            {
                'leg_id': 'leg_1',
                'option_type': 'PE',
                'strike_price': atm_price - 300,  # Buy Put (OTM)
                'action': 'BUY',
                'quantity': self.supported_underlyings[underlying]['lot_size'],
                'order_type': 'MARKET'
            },
            {
                'leg_id': 'leg_2',
                'option_type': 'PE', 
                'strike_price': atm_price - 100,  # Sell Put (closer to ATM)
                'action': 'SELL',
                'quantity': self.supported_underlyings[underlying]['lot_size'],
                'order_type': 'MARKET'
            },
            {
                'leg_id': 'leg_3',
                'option_type': 'CE',
                'strike_price': atm_price + 100,  # Sell Call (closer to ATM)
                'action': 'SELL',
                'quantity': self.supported_underlyings[underlying]['lot_size'],
                'order_type': 'MARKET'
            },
            {
                'leg_id': 'leg_4',
                'option_type': 'CE',
                'strike_price': atm_price + 300,  # Buy Call (OTM)
                'action': 'BUY',
                'quantity': self.supported_underlyings[underlying]['lot_size'],
                'order_type': 'MARKET'
            }
        ]
        
        return self.create_sample_strategy(
            strategy_name=strategy_name,
            underlying=underlying,
            entry_time=entry_time,
            exit_time=exit_time,
            entry_days=entry_days,
            exit_days=entry_days,
            legs=legs
        )
        
    def create_long_straddle_strategy(self,
                                    strategy_name: str = "Test Long Straddle",
                                    underlying: str = "NIFTY", 
                                    entry_time: str = "09:30",
                                    exit_time: str = "15:20",
                                    atm_price: Decimal = Decimal('19500')) -> str:
        """Create a Long Straddle options strategy for testing"""
        
        # Long Straddle: Buy Call + Buy Put at same strike (ATM)
        legs = [
            {
                'leg_id': 'leg_1',
                'option_type': 'CE',
                'strike_price': atm_price,  # Buy Call ATM
                'action': 'BUY',
                'quantity': self.supported_underlyings[underlying]['lot_size'],
                'order_type': 'MARKET'
            },
            {
                'leg_id': 'leg_2',
                'option_type': 'PE',
                'strike_price': atm_price,  # Buy Put ATM
                'action': 'BUY', 
                'quantity': self.supported_underlyings[underlying]['lot_size'],
                'order_type': 'MARKET'
            }
        ]
        
        return self.create_sample_strategy(
            strategy_name=strategy_name,
            underlying=underlying,
            entry_time=entry_time,
            exit_time=exit_time,
            legs=legs
        )
        
    def create_bull_call_spread_strategy(self,
                                       strategy_name: str = "Test Bull Call Spread",
                                       underlying: str = "NIFTY",
                                       entry_time: str = "10:00", 
                                       exit_time: str = "15:15",
                                       atm_price: Decimal = Decimal('19500')) -> str:
        """Create a Bull Call Spread options strategy for testing"""
        
        # Bull Call Spread: Buy Call (ITM/ATM) + Sell Call (OTM)
        legs = [
            {
                'leg_id': 'leg_1',
                'option_type': 'CE',
                'strike_price': atm_price - 100,  # Buy Call (closer to ITM)
                'action': 'BUY',
                'quantity': self.supported_underlyings[underlying]['lot_size'],
                'order_type': 'MARKET'
            },
            {
                'leg_id': 'leg_2',
                'option_type': 'CE',
                'strike_price': atm_price + 200,  # Sell Call (OTM)
                'action': 'SELL',
                'quantity': self.supported_underlyings[underlying]['lot_size'],
                'order_type': 'MARKET'
            }
        ]
        
        return self.create_sample_strategy(
            strategy_name=strategy_name,
            underlying=underlying,
            entry_time=entry_time,
            exit_time=exit_time,
            legs=legs
        )
        
    def create_weekend_test_strategy(self,
                                   strategy_name: str = "Weekend Test Strategy", 
                                   underlying: str = "NIFTY",
                                   entry_time: str = "10:00") -> str:
        """Create a strategy that should be skipped on weekends"""
        
        return self.create_sample_strategy(
            strategy_name=strategy_name,
            underlying=underlying,
            entry_time=entry_time,
            exit_time="15:00",
            entry_days=['SATURDAY', 'SUNDAY'],  # Should be skipped
            exit_days=['SATURDAY', 'SUNDAY'],
            legs=self.get_default_iron_condor_legs()
        )
        
    def create_multi_weekday_strategy(self,
                                    strategy_name: str = "Multi Weekday Strategy",
                                    underlying: str = "BANKNIFTY",
                                    entry_time: str = "14:00") -> str:
        """Create a strategy with different entry and exit days for testing"""
        
        return self.create_sample_strategy(
            strategy_name=strategy_name,
            underlying=underlying,
            entry_time=entry_time,
            exit_time="15:15",
            entry_days=['MONDAY', 'WEDNESDAY', 'FRIDAY'],  # MWF entry
            exit_days=['TUESDAY', 'THURSDAY'],              # T-Th exit  
            legs=self.get_default_iron_condor_legs()
        )
        
    def get_overlap_test_strategies(self) -> List[str]:
        """Create strategies for testing overlap prevention (18:20 window issue)"""
        
        strategies = []
        
        # Strategy A: Should be discovered in 18:15-18:20 window (excluding 18:20)
        strategy_a = self.create_sample_strategy(
            strategy_name="Overlap Test Strategy A",
            underlying="NIFTY",
            entry_time="18:19",  # Should be in first window
            exit_time="18:30",
            entry_days=['THURSDAY'],
            legs=self.get_default_iron_condor_legs()
        )
        strategies.append(strategy_a)
        
        # Strategy B: Should be discovered in 18:20-18:25 window (including 18:20)
        strategy_b = self.create_sample_strategy(
            strategy_name="Overlap Test Strategy B", 
            underlying="BANKNIFTY",
            entry_time="18:20",  # Should be in second window only
            exit_time="18:35",
            entry_days=['THURSDAY'],
            legs=self.get_default_iron_condor_legs()
        )
        strategies.append(strategy_b)
        
        return strategies
        
    def validate_options_leg_structure(self, leg: Dict[str, Any]) -> bool:
        """Validate that an options leg has proper structure"""
        required_fields = ['leg_id', 'option_type', 'strike_price', 'action', 'quantity', 'order_type']
        
        for field in required_fields:
            if field not in leg:
                return False
                
        # Validate option_type
        if leg['option_type'] not in ['CE', 'PE']:
            return False
            
        # Validate action
        if leg['action'] not in ['BUY', 'SELL']:
            return False
            
        # Validate order_type
        if leg['order_type'] not in ['MARKET', 'LIMIT', 'SL', 'SL-M']:
            return False
            
        return True
        
    def validate_strategy_risk_profile(self, legs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze strategy risk profile for testing"""
        
        total_premium = Decimal('0')
        max_profit = Decimal('0')
        max_loss = Decimal('0')
        
        buy_legs = [leg for leg in legs if leg['action'] == 'BUY']
        sell_legs = [leg for leg in legs if leg['action'] == 'SELL']
        
        return {
            'total_legs': len(legs),
            'buy_legs': len(buy_legs),
            'sell_legs': len(sell_legs),
            'net_premium': total_premium,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'is_credit_spread': len(sell_legs) > len(buy_legs),
            'is_debit_spread': len(buy_legs) > len(sell_legs)
        }
        
    def get_expiry_dates_for_testing(self, underlying: str, num_weeks: int = 4) -> List[str]:
        """Generate expiry dates for testing based on underlying"""
        
        expiry_day = self.supported_underlyings[underlying]['expiry_day']
        # This would normally calculate actual expiry dates
        # For testing, return mock dates
        
        return [
            "2025-09-05",  # This week
            "2025-09-12",  # Next week
            "2025-09-19",  # Week after
            "2025-09-26"   # Monthly expiry
        ]
        
    def assert_iron_condor_structure(self, legs: List[Dict[str, Any]]):
        """Assert that legs form a valid Iron Condor structure"""
        self.assertEqual(len(legs), 4, "Iron Condor should have exactly 4 legs")
        
        # Should have 2 puts and 2 calls
        puts = [leg for leg in legs if leg['option_type'] == 'PE']
        calls = [leg for leg in legs if leg['option_type'] == 'CE']
        
        self.assertEqual(len(puts), 2, "Iron Condor should have 2 put legs")
        self.assertEqual(len(calls), 2, "Iron Condor should have 2 call legs")
        
    def assert_straddle_structure(self, legs: List[Dict[str, Any]]):
        """Assert that legs form a valid Straddle structure"""
        self.assertEqual(len(legs), 2, "Straddle should have exactly 2 legs")
        
        # Should have 1 call and 1 put at same strike
        call_leg = next((leg for leg in legs if leg['option_type'] == 'CE'), None)
        put_leg = next((leg for leg in legs if leg['option_type'] == 'PE'), None)
        
        self.assertIsNotNone(call_leg, "Straddle should have a call leg")
        self.assertIsNotNone(put_leg, "Straddle should have a put leg")
        self.assertEqual(call_leg['strike_price'], put_leg['strike_price'], 
                        "Straddle legs should have same strike price")