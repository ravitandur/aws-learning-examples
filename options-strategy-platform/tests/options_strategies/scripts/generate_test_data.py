#!/usr/bin/env python3
"""
Options Strategy Test Data Generator

Generates comprehensive test data for the options trading platform:
- Sample baskets with Indian market specialization
- Multi-strategy configurations (Iron Condor, Straddles, Spreads)
- Multi-broker allocation scenarios
- Realistic market data and pricing
- Historical execution scenarios

Usage:
    python generate_test_data.py [--data-type all|baskets|strategies|market] [--volume low|medium|high]
"""

import sys
import os
import argparse
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
import random

# Add paths for test discovery
current_dir = os.path.dirname(os.path.abspath(__file__))
tests_root = os.path.join(current_dir, '..', '..')
options_tests_dir = os.path.join(tests_root, 'options_strategies')
sys.path.append(tests_root)
sys.path.append(options_tests_dir)

from strategy_flow.fixtures.OptionsStrategyTestBase import OptionsStrategyTestBase


class OptionsStrategyTestDataGenerator(OptionsStrategyTestBase):
    """
    Test data generator for options strategy platform.
    Creates realistic test scenarios for comprehensive testing.
    """
    
    def __init__(self):
        super().__init__()
        self.generated_data = {
            'baskets': [],
            'strategies': [],
            'broker_allocations': [],
            'market_data': {},
            'execution_history': []
        }
        
    def generate_comprehensive_test_data(self, data_type: str = 'all', volume: str = 'medium') -> Dict[str, Any]:
        """Generate comprehensive test data based on parameters"""
        
        print(f"🚀 Generating Options Strategy Test Data")
        print(f"📊 Data Type: {data_type.upper()}, Volume: {volume.upper()}")
        print("="*60)
        
        # Setup test environment
        self.setUp()
        
        # Generate data based on type
        if data_type in ['all', 'baskets']:
            print("\n📋 Generating Sample Baskets...")
            self.generate_sample_baskets(volume)
            
        if data_type in ['all', 'strategies']:
            print("\n🎯 Generating Strategy Configurations...")
            self.generate_strategy_configurations(volume)
            
        if data_type in ['all', 'market']:
            print("\n📈 Generating Market Data...")
            self.generate_market_data_scenarios(volume)
            
        # Save generated data
        self.save_generated_data()
        
        print(f"\n✅ Test data generation completed successfully!")
        return self.generated_data
        
    def generate_sample_baskets(self, volume: str):
        """Generate sample baskets with different scenarios"""
        
        volume_configs = {
            'low': 5,
            'medium': 15,
            'high': 50
        }
        
        basket_count = volume_configs.get(volume, 15)
        
        # Basket scenarios for comprehensive testing
        basket_scenarios = [
            {
                'name': 'Conservative Income Strategies',
                'description': 'Low-risk income generation through covered calls and cash-secured puts',
                'risk_level': 'LOW',
                'expected_return': 8.5
            },
            {
                'name': 'Neutral Market Strategies',
                'description': 'Market-neutral strategies using Iron Condors and Straddles',
                'risk_level': 'MEDIUM',
                'expected_return': 15.2
            },
            {
                'name': 'Aggressive Growth Strategies',
                'description': 'High-growth potential using directional spreads and leveraged positions',
                'risk_level': 'HIGH',
                'expected_return': 28.7
            },
            {
                'name': 'Indian Market Specialists',
                'description': 'Strategies optimized for NIFTY, BANKNIFTY, and FINNIFTY',
                'risk_level': 'MEDIUM',
                'expected_return': 18.9
            },
            {
                'name': 'Multi-Broker Diversification',
                'description': 'Risk distribution across multiple brokers for safety',
                'risk_level': 'LOW',
                'expected_return': 12.4
            },
            {
                'name': 'High-Frequency Trading',
                'description': 'Short-term strategies with multiple daily executions',
                'risk_level': 'HIGH',
                'expected_return': 35.6
            }
        ]
        
        for i in range(basket_count):
            scenario = basket_scenarios[i % len(basket_scenarios)]
            
            # Create unique basket name
            basket_name = f"{scenario['name']} {i+1}" if basket_count > len(basket_scenarios) else scenario['name']
            
            basket_id = self.create_sample_basket(basket_name)
            
            basket_data = {
                'basket_id': basket_id,
                'basket_name': basket_name,
                'description': scenario['description'],
                'risk_level': scenario['risk_level'],
                'expected_return_percentage': scenario['expected_return'],
                'created_at': datetime.now().isoformat(),
                'strategies_count': 0,  # Will be updated when strategies are added
                'total_capital_allocation': 0
            }
            
            self.generated_data['baskets'].append(basket_data)
            
            print(f"   ✅ Created basket: {basket_name}")
            
    def generate_strategy_configurations(self, volume: str):
        """Generate strategy configurations with diverse scenarios"""
        
        volume_configs = {
            'low': {'strategies_per_basket': 2, 'total_strategies': 10},
            'medium': {'strategies_per_basket': 3, 'total_strategies': 45},
            'high': {'strategies_per_basket': 5, 'total_strategies': 250}
        }
        
        config = volume_configs.get(volume, volume_configs['medium'])
        
        if not self.generated_data['baskets']:
            print("   ⚠️  No baskets found, generating default basket...")
            self.generate_sample_baskets('low')
            
        # Strategy templates for different scenarios
        strategy_templates = [
            {
                'type': 'IRON_CONDOR',
                'name': 'Weekly Iron Condor',
                'underlying': 'NIFTY',
                'complexity': 'HIGH',
                'legs': 4,
                'typical_duration_days': 7
            },
            {
                'type': 'BULL_CALL_SPREAD',
                'name': 'Bull Call Spread',
                'underlying': 'BANKNIFTY', 
                'complexity': 'MEDIUM',
                'legs': 2,
                'typical_duration_days': 14
            },
            {
                'type': 'STRADDLE',
                'name': 'Long Straddle',
                'underlying': 'FINNIFTY',
                'complexity': 'MEDIUM',
                'legs': 2,
                'typical_duration_days': 21
            },
            {
                'type': 'COVERED_CALL',
                'name': 'Covered Call',
                'underlying': 'SENSEX',
                'complexity': 'LOW',
                'legs': 1,
                'typical_duration_days': 30
            },
            {
                'type': 'PUT_SPREAD',
                'name': 'Bear Put Spread',
                'underlying': 'MIDCPNIFTY',
                'complexity': 'MEDIUM', 
                'legs': 2,
                'typical_duration_days': 10
            }
        ]
        
        # Generate strategies for each basket
        for basket in self.generated_data['baskets']:
            basket_id = basket['basket_id']
            strategies_to_create = config['strategies_per_basket']
            
            for i in range(strategies_to_create):
                template = strategy_templates[i % len(strategy_templates)]
                
                # Create strategy based on template
                strategy_data = self.create_strategy_from_template(basket_id, template, i+1)
                
                # Generate multi-broker allocations
                broker_allocations = self.generate_broker_allocations(strategy_data)
                strategy_data['broker_allocations'] = broker_allocations
                
                self.generated_data['strategies'].append(strategy_data)
                
                print(f"   ✅ Created strategy: {strategy_data['strategy_name']}")
                
            # Update basket with strategy count
            basket['strategies_count'] = strategies_to_create
            
    def generate_market_data_scenarios(self, volume: str):
        """Generate realistic market data scenarios"""
        
        volume_configs = {
            'low': 5,
            'medium': 20, 
            'high': 100
        }
        
        scenario_count = volume_configs.get(volume, 20)
        
        # Indian market indices with realistic parameters
        indian_indices = {
            'NIFTY': {
                'current_price': 19850.0,
                'volatility_range': (12.0, 25.0),
                'daily_change_range': (-2.5, 2.5),
                'lot_size': 25
            },
            'BANKNIFTY': {
                'current_price': 44750.0,
                'volatility_range': (15.0, 35.0),
                'daily_change_range': (-3.0, 3.0),
                'lot_size': 15
            },
            'FINNIFTY': {
                'current_price': 19980.0,
                'volatility_range': (14.0, 28.0),
                'daily_change_range': (-2.8, 2.8),
                'lot_size': 25
            },
            'SENSEX': {
                'current_price': 66350.0,
                'volatility_range': (10.0, 22.0),
                'daily_change_range': (-2.0, 2.0),
                'lot_size': 10
            },
            'MIDCPNIFTY': {
                'current_price': 9750.0,
                'volatility_range': (16.0, 30.0),
                'daily_change_range': (-3.5, 3.5),
                'lot_size': 75
            }
        }
        
        # Generate market scenarios for different dates
        base_date = datetime.now().date()
        
        for i in range(scenario_count):
            scenario_date = base_date + timedelta(days=i)
            daily_scenarios = {}
            
            for index, params in indian_indices.items():
                # Generate realistic market data for this index
                scenario = self.generate_index_market_scenario(index, params, scenario_date)
                daily_scenarios[index] = scenario
                
            self.generated_data['market_data'][scenario_date.isoformat()] = daily_scenarios
            
        print(f"   ✅ Generated market data for {scenario_count} scenarios")
        
    def create_strategy_from_template(self, basket_id: str, template: Dict[str, Any], sequence: int) -> Dict[str, Any]:
        """Create a strategy based on template"""
        
        # Generate realistic entry/exit times
        entry_times = ['09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00']
        exit_times = ['15:15', '15:20', '15:25']
        
        # Generate weekdays based on strategy type
        if template['type'] == 'IRON_CONDOR':
            entry_days = ['MONDAY', 'WEDNESDAY', 'FRIDAY']
        elif template['type'] in ['BULL_CALL_SPREAD', 'PUT_SPREAD']:
            entry_days = ['TUESDAY', 'THURSDAY']
        else:
            entry_days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
            
        # Create strategy name
        strategy_name = f"{template['name']} {template['underlying']} {sequence}"
        
        # Create strategy based on type
        if template['type'] == 'IRON_CONDOR':
            strategy_id = self.create_iron_condor_strategy(
                strategy_name=strategy_name,
                underlying=template['underlying'],
                entry_time=random.choice(entry_times),
                entry_days=entry_days
            )
        elif template['type'] == 'BULL_CALL_SPREAD':
            strategy_id = self.create_bull_call_spread_strategy(
                strategy_name=strategy_name,
                underlying=template['underlying'],
                entry_time=random.choice(entry_times),
                entry_days=entry_days
            )
        else:
            strategy_id = self.create_sample_strategy(
                strategy_name=strategy_name,
                underlying=template['underlying'],
                entry_time=random.choice(entry_times),
                entry_days=entry_days
            )
            
        # Get strategy details
        strategy = self.get_strategy_details(strategy_id)
        legs = self.get_strategy_legs(strategy_id)
        
        strategy_data = {
            'strategy_id': strategy_id,
            'basket_id': basket_id,
            'strategy_name': strategy_name,
            'strategy_type': template['type'],
            'underlying': template['underlying'],
            'complexity': template['complexity'],
            'legs_count': len(legs),
            'entry_time': strategy.get('entry_time'),
            'entry_days': entry_days,
            'typical_duration_days': template['typical_duration_days'],
            'created_at': datetime.now().isoformat(),
            'legs': legs
        }
        
        return strategy_data
        
    def generate_broker_allocations(self, strategy_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate realistic multi-broker allocations"""
        
        strategy_id = strategy_data['strategy_id']
        legs_count = strategy_data['legs_count']
        
        # Different allocation scenarios based on strategy complexity
        if strategy_data['complexity'] == 'LOW':
            # Simple single broker allocation
            allocation = self.add_broker_allocation_to_strategy(
                strategy_id=strategy_id,
                broker_name='zerodha',
                lots_allocation=random.randint(2, 8),
                leg_numbers=list(range(1, legs_count + 1))
            )
            
            return [self.get_broker_allocation_details(allocation)]
            
        elif strategy_data['complexity'] == 'MEDIUM':
            # Two broker allocation
            brokers = ['zerodha', 'angel_one']
            allocations = []
            
            # Split legs between brokers
            legs_per_broker = legs_count // 2
            
            for i, broker in enumerate(brokers):
                start_leg = i * legs_per_broker + 1
                end_leg = start_leg + legs_per_broker - 1 if i == 0 else legs_count
                
                leg_numbers = list(range(start_leg, end_leg + 1))
                
                allocation = self.add_broker_allocation_to_strategy(
                    strategy_id=strategy_id,
                    broker_name=broker,
                    lots_allocation=random.randint(2, 6),
                    leg_numbers=leg_numbers
                )
                
                allocations.append(self.get_broker_allocation_details(allocation))
                
            return allocations
            
        else:  # HIGH complexity
            # Three broker allocation for maximum diversification
            brokers = ['zerodha', 'angel_one', 'finvasia']
            allocations = []
            
            # Distribute legs across brokers
            if legs_count == 4:  # Iron Condor
                leg_distributions = [
                    [1, 2],  # Call spread
                    [3, 4],  # Put spread
                    []       # No legs for third broker in 4-leg strategy
                ]
            else:
                # Distribute evenly
                legs_per_broker = max(1, legs_count // len(brokers))
                leg_distributions = []
                for i in range(len(brokers)):
                    start_leg = i * legs_per_broker + 1
                    end_leg = min(start_leg + legs_per_broker - 1, legs_count)
                    if start_leg <= legs_count:
                        leg_distributions.append(list(range(start_leg, end_leg + 1)))
                    else:
                        leg_distributions.append([])
                        
            for i, (broker, leg_numbers) in enumerate(zip(brokers, leg_distributions)):
                if leg_numbers:  # Only create allocation if there are legs
                    allocation = self.add_broker_allocation_to_strategy(
                        strategy_id=strategy_id,
                        broker_name=broker,
                        lots_allocation=random.randint(1, 4),
                        leg_numbers=leg_numbers
                    )
                    
                    allocations.append(self.get_broker_allocation_details(allocation))
                    
            return allocations
            
    def generate_index_market_scenario(self, index: str, params: Dict[str, Any], scenario_date) -> Dict[str, Any]:
        """Generate realistic market scenario for an index"""
        
        base_price = params['current_price']
        vol_min, vol_max = params['volatility_range']
        change_min, change_max = params['daily_change_range']
        
        # Generate market scenario
        daily_change_pct = random.uniform(change_min, change_max)
        current_price = base_price * (1 + daily_change_pct / 100)
        
        volatility = random.uniform(vol_min, vol_max)
        
        # Generate options chain data
        options_chain = self.generate_options_chain(current_price, volatility, index)
        
        scenario = {
            'index': index,
            'date': scenario_date.isoformat(),
            'current_price': round(current_price, 2),
            'daily_change_percentage': round(daily_change_pct, 2),
            'implied_volatility': round(volatility, 2),
            'lot_size': params['lot_size'],
            'options_chain': options_chain,
            'market_phase': self.determine_market_phase(datetime.now().time()),
            'volume_profile': random.choice(['LOW', 'MEDIUM', 'HIGH']),
            'market_sentiment': random.choice(['BULLISH', 'BEARISH', 'NEUTRAL'])
        }
        
        return scenario
        
    def generate_options_chain(self, spot_price: float, volatility: float, index: str) -> List[Dict[str, Any]]:
        """Generate realistic options chain data"""
        
        options_chain = []
        
        # Generate strikes around current price
        if index in ['NIFTY', 'FINNIFTY']:
            strike_interval = 50
        elif index == 'BANKNIFTY':
            strike_interval = 100
        elif index == 'SENSEX':
            strike_interval = 100
        else:  # MIDCPNIFTY
            strike_interval = 25
            
        # Generate 10 strikes above and below current price
        for i in range(-10, 11):
            strike = int(spot_price + (i * strike_interval))
            
            # Calculate realistic option premiums (simplified Black-Scholes approximation)
            call_premium = self.calculate_option_premium(spot_price, strike, volatility, 'CALL')
            put_premium = self.calculate_option_premium(spot_price, strike, volatility, 'PUT')
            
            options_chain.extend([
                {
                    'strike_price': strike,
                    'option_type': 'CALL',
                    'premium': round(call_premium, 2),
                    'implied_volatility': round(volatility + random.uniform(-2, 2), 2),
                    'delta': round(self.calculate_delta(spot_price, strike, 'CALL'), 4),
                    'gamma': round(random.uniform(0.001, 0.01), 4),
                    'theta': round(random.uniform(-0.5, -0.1), 4),
                    'vega': round(random.uniform(0.1, 0.3), 4)
                },
                {
                    'strike_price': strike,
                    'option_type': 'PUT',
                    'premium': round(put_premium, 2),
                    'implied_volatility': round(volatility + random.uniform(-2, 2), 2),
                    'delta': round(self.calculate_delta(spot_price, strike, 'PUT'), 4),
                    'gamma': round(random.uniform(0.001, 0.01), 4),
                    'theta': round(random.uniform(-0.5, -0.1), 4),
                    'vega': round(random.uniform(0.1, 0.3), 4)
                }
            ])
            
        return options_chain
        
    def calculate_option_premium(self, spot: float, strike: float, volatility: float, option_type: str) -> float:
        """Calculate simplified option premium"""
        
        # Simplified premium calculation (not actual Black-Scholes)
        intrinsic_value = 0
        
        if option_type == 'CALL':
            intrinsic_value = max(0, spot - strike)
        else:  # PUT
            intrinsic_value = max(0, strike - spot)
            
        # Time value based on distance from strike and volatility
        distance = abs(spot - strike) / spot
        time_value = (volatility / 100) * spot * (0.3 - distance) * random.uniform(0.5, 1.5)
        time_value = max(0, time_value)
        
        return intrinsic_value + time_value
        
    def calculate_delta(self, spot: float, strike: float, option_type: str) -> float:
        """Calculate simplified delta"""
        
        if option_type == 'CALL':
            if spot > strike:
                return random.uniform(0.5, 0.9)
            else:
                return random.uniform(0.1, 0.5)
        else:  # PUT
            if spot < strike:
                return random.uniform(-0.9, -0.5)
            else:
                return random.uniform(-0.5, -0.1)
                
    def determine_market_phase(self, current_time) -> str:
        """Determine market phase based on time"""
        
        hour = current_time.hour
        minute = current_time.minute
        
        if (hour == 9 and minute >= 15) or (hour == 10 and minute < 30):
            return 'MARKET_OPEN'
        elif hour >= 10 and hour < 13:
            return 'ACTIVE_TRADING'
        elif hour >= 13 and hour < 14:
            return 'LUNCH_BREAK'
        elif hour >= 14 and hour < 15:
            return 'ACTIVE_TRADING'
        elif hour == 15 and minute >= 20:
            return 'PRE_CLOSE'
        else:
            return 'MARKET_CLOSED'
            
    def get_broker_allocation_details(self, allocation_id: str) -> Dict[str, Any]:
        """Get detailed broker allocation information"""
        
        # This would typically query the database
        # For test data generation, return mock data
        return {
            'allocation_id': allocation_id,
            'broker_name': random.choice(['zerodha', 'angel_one', 'finvasia']),
            'lots_allocation': random.randint(1, 8),
            'leg_numbers': [1, 2],
            'created_at': datetime.now().isoformat()
        }
        
    def save_generated_data(self):
        """Save generated test data to files"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_dir = os.path.join(current_dir, '..', 'test_data', 'generated')
        
        os.makedirs(data_dir, exist_ok=True)
        
        # Save comprehensive data file
        comprehensive_file = os.path.join(data_dir, f'comprehensive_test_data_{timestamp}.json')
        
        with open(comprehensive_file, 'w') as f:
            json.dump(self.generated_data, f, indent=2, default=str)
            
        # Save individual data type files
        for data_type, data in self.generated_data.items():
            if data:  # Only save if there's data
                type_file = os.path.join(data_dir, f'{data_type}_test_data_{timestamp}.json')
                
                with open(type_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                    
        print(f"\n📄 Test data saved to: {data_dir}")
        print(f"   📊 Comprehensive data: comprehensive_test_data_{timestamp}.json")
        
        # Print summary
        print(f"\n📋 Generated Data Summary:")
        print(f"   🗂️  Baskets: {len(self.generated_data['baskets'])}")
        print(f"   🎯 Strategies: {len(self.generated_data['strategies'])}")
        print(f"   🏦 Broker Allocations: {sum(len(s.get('broker_allocations', [])) for s in self.generated_data['strategies'])}")
        print(f"   📈 Market Scenarios: {len(self.generated_data['market_data'])}")


def main():
    """Main entry point for test data generation"""
    
    parser = argparse.ArgumentParser(
        description='Options Strategy Test Data Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_test_data.py                           # Generate all data types (medium volume)
  python generate_test_data.py --data-type baskets       # Generate only baskets
  python generate_test_data.py --volume high             # Generate high volume data
  python generate_test_data.py --data-type strategies --volume low
        """
    )
    
    parser.add_argument(
        '--data-type',
        choices=['all', 'baskets', 'strategies', 'market'],
        default='all',
        help='Type of data to generate (default: all)'
    )
    
    parser.add_argument(
        '--volume',
        choices=['low', 'medium', 'high'],
        default='medium',
        help='Volume of data to generate (default: medium)'
    )
    
    args = parser.parse_args()
    
    # Generate test data
    generator = OptionsStrategyTestDataGenerator()
    
    try:
        results = generator.generate_comprehensive_test_data(
            data_type=args.data_type,
            volume=args.volume
        )
        
        print("\n🎉 Test data generation completed successfully!")
        
    except Exception as e:
        print(f"❌ Test data generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()