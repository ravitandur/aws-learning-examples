"""
Risk Calculation Utilities
Shared utilities for options trading risk management and calculations
"""

import math
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, getcontext
from dataclasses import dataclass
from datetime import datetime, timedelta

# Set precision for decimal calculations
getcontext().prec = 10


@dataclass
class OptionGreeks:
    """Option Greeks data structure"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


@dataclass
class PositionRisk:
    """Position risk metrics"""
    max_loss: Decimal
    max_profit: Decimal
    breakeven_points: List[float]
    probability_of_profit: float
    risk_reward_ratio: float


class RiskCalculator:
    """Advanced risk calculation utilities for options trading"""
    
    def __init__(self):
        self.risk_free_rate = 0.06  # 6% risk-free rate for India
    
    def black_scholes_call(self, spot: float, strike: float, time_to_expiry: float, 
                          volatility: float, risk_free_rate: Optional[float] = None) -> float:
        """
        Calculate Black-Scholes call option price
        
        Args:
            spot: Current spot price
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (annual)
            risk_free_rate: Risk-free rate (defaults to instance default)
        
        Returns:
            Call option theoretical price
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if time_to_expiry <= 0:
            return max(0, spot - strike)
        
        d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
        d2 = d1 - volatility * math.sqrt(time_to_expiry)
        
        call_price = spot * self._norm_cdf(d1) - strike * math.exp(-risk_free_rate * time_to_expiry) * self._norm_cdf(d2)
        return max(0, call_price)
    
    def black_scholes_put(self, spot: float, strike: float, time_to_expiry: float, 
                         volatility: float, risk_free_rate: Optional[float] = None) -> float:
        """Calculate Black-Scholes put option price"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if time_to_expiry <= 0:
            return max(0, strike - spot)
        
        d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
        d2 = d1 - volatility * math.sqrt(time_to_expiry)
        
        put_price = strike * math.exp(-risk_free_rate * time_to_expiry) * self._norm_cdf(-d2) - spot * self._norm_cdf(-d1)
        return max(0, put_price)
    
    def calculate_greeks(self, spot: float, strike: float, time_to_expiry: float, 
                        volatility: float, option_type: str = 'call', 
                        risk_free_rate: Optional[float] = None) -> OptionGreeks:
        """
        Calculate option Greeks
        
        Args:
            spot: Current spot price
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility
            option_type: 'call' or 'put'
            risk_free_rate: Risk-free rate
        
        Returns:
            OptionGreeks object with all Greeks
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if time_to_expiry <= 0:
            return OptionGreeks(0, 0, 0, 0, 0)
        
        d1 = (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
        d2 = d1 - volatility * math.sqrt(time_to_expiry)
        
        # Common calculations
        nd1 = self._norm_cdf(d1)
        nd2 = self._norm_cdf(d2)
        npd1 = self._norm_pdf(d1)
        
        if option_type.lower() == 'call':
            delta = nd1
            rho = strike * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * nd2 / 100
        else:  # put
            delta = nd1 - 1
            rho = -strike * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * self._norm_cdf(-d2) / 100
        
        gamma = npd1 / (spot * volatility * math.sqrt(time_to_expiry))
        theta = (-spot * npd1 * volatility / (2 * math.sqrt(time_to_expiry)) - 
                risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry) * 
                (nd2 if option_type.lower() == 'call' else self._norm_cdf(-d2))) / 365
        vega = spot * npd1 * math.sqrt(time_to_expiry) / 100
        
        return OptionGreeks(
            delta=round(delta, 4),
            gamma=round(gamma, 6),
            theta=round(theta, 4),
            vega=round(vega, 4),
            rho=round(rho, 4)
        )
    
    def calculate_portfolio_greeks(self, positions: List[Dict]) -> OptionGreeks:
        """
        Calculate portfolio-level Greeks
        
        Args:
            positions: List of positions with Greeks and quantities
        
        Returns:
            Aggregated portfolio Greeks
        """
        total_delta = total_gamma = total_theta = total_vega = total_rho = 0
        
        for position in positions:
            quantity = position.get('quantity', 0)
            greeks = position.get('greeks', {})
            
            total_delta += quantity * greeks.get('delta', 0)
            total_gamma += quantity * greeks.get('gamma', 0)
            total_theta += quantity * greeks.get('theta', 0)
            total_vega += quantity * greeks.get('vega', 0)
            total_rho += quantity * greeks.get('rho', 0)
        
        return OptionGreeks(
            delta=round(total_delta, 4),
            gamma=round(total_gamma, 6),
            theta=round(total_theta, 4),
            vega=round(total_vega, 4),
            rho=round(total_rho, 4)
        )
    
    def calculate_strategy_payoff(self, legs: List[Dict], spot_prices: List[float]) -> Dict:
        """
        Calculate payoff for multi-leg strategy
        
        Args:
            legs: List of strategy legs with strike, option_type, transaction_type, quantity
            spot_prices: List of spot prices to calculate payoff for
        
        Returns:
            Dict with payoff data and analysis
        """
        payoffs = []
        
        for spot in spot_prices:
            total_payoff = 0
            
            for leg in legs:
                strike = leg['strike']
                option_type = leg['option_type'].upper()
                transaction_type = leg['transaction_type'].upper()  # BUY/SELL
                quantity = leg['quantity']
                entry_premium = leg.get('entry_premium', 0)
                
                # Calculate intrinsic value at expiry
                if option_type == 'CE':  # Call
                    intrinsic_value = max(0, spot - strike)
                else:  # Put
                    intrinsic_value = max(0, strike - spot)
                
                # Calculate leg P&L
                if transaction_type == 'BUY':
                    leg_pnl = quantity * (intrinsic_value - entry_premium)
                else:  # SELL
                    leg_pnl = quantity * (entry_premium - intrinsic_value)
                
                total_payoff += leg_pnl
            
            payoffs.append({
                'spot_price': spot,
                'payoff': round(total_payoff, 2)
            })
        
        # Calculate key metrics
        max_profit = max(p['payoff'] for p in payoffs)
        max_loss = min(p['payoff'] for p in payoffs)
        
        # Find breakeven points
        breakeven_points = self._find_breakeven_points(payoffs)
        
        return {
            'payoffs': payoffs,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'breakeven_points': breakeven_points,
            'risk_reward_ratio': abs(max_profit / max_loss) if max_loss != 0 else float('inf')
        }
    
    def calculate_position_sizing(self, account_balance: Decimal, risk_percentage: float, 
                                max_loss_per_trade: Decimal, strategy_max_loss: Decimal) -> Dict:
        """
        Calculate appropriate position sizing based on risk parameters
        
        Args:
            account_balance: Total account balance
            risk_percentage: Maximum risk per trade as percentage
            max_loss_per_trade: Maximum absolute loss per trade
            strategy_max_loss: Maximum loss for this specific strategy
        
        Returns:
            Position sizing recommendations
        """
        # Calculate maximum risk amount based on percentage
        max_risk_by_percentage = account_balance * Decimal(risk_percentage / 100)
        
        # Use the most conservative limit
        actual_max_risk = min(max_risk_by_percentage, max_loss_per_trade, strategy_max_loss)
        
        # Calculate position size multiplier
        if strategy_max_loss > 0:
            position_multiplier = actual_max_risk / strategy_max_loss
        else:
            position_multiplier = Decimal('1')
        
        return {
            'max_risk_amount': float(actual_max_risk),
            'position_multiplier': float(position_multiplier),
            'recommended_lots': max(1, int(position_multiplier)),
            'risk_percentage_used': float((actual_max_risk / account_balance) * 100),
            'max_risk_by_percentage': float(max_risk_by_percentage),
            'limiting_factor': self._determine_limiting_factor(
                max_risk_by_percentage, max_loss_per_trade, strategy_max_loss
            )
        }
    
    def calculate_margin_requirement(self, legs: List[Dict], underlying_price: float) -> Dict:
        """
        Calculate margin requirement for option strategy (SPAN + Exposure)
        Note: This is a simplified calculation. Actual margin requirements 
        would need integration with broker APIs.
        """
        total_span_margin = Decimal('0')
        total_exposure_margin = Decimal('0')
        
        for leg in legs:
            strike = leg['strike']
            option_type = leg['option_type'].upper()
            transaction_type = leg['transaction_type'].upper()
            quantity = leg['quantity']
            lot_size = leg.get('lot_size', 25)  # Default NIFTY lot size
            
            notional_value = Decimal(str(underlying_price * quantity * lot_size))
            
            if transaction_type == 'SELL':
                # Simplified SPAN margin calculation (actual would be more complex)
                if option_type == 'CE':
                    span_margin = notional_value * Decimal('0.10')  # 10% for ITM calls
                else:
                    span_margin = notional_value * Decimal('0.12')  # 12% for puts
                
                exposure_margin = notional_value * Decimal('0.05')  # 5% exposure margin
                
                total_span_margin += span_margin
                total_exposure_margin += exposure_margin
        
        total_margin = total_span_margin + total_exposure_margin
        
        return {
            'span_margin': float(total_span_margin),
            'exposure_margin': float(total_exposure_margin),
            'total_margin': float(total_margin),
            'margin_blocked': float(total_margin),
            'currency': 'INR'
        }
    
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> Dict:
        """
        Calculate Value at Risk (VaR) for given returns
        
        Args:
            returns: Historical returns data
            confidence_level: Confidence level (default 95%)
        
        Returns:
            VaR calculations
        """
        if not returns:
            return {'var_95': 0, 'var_99': 0, 'expected_shortfall': 0}
        
        sorted_returns = sorted(returns)
        n = len(sorted_returns)
        
        # Calculate VaR at different confidence levels
        var_95_index = int((1 - 0.95) * n)
        var_99_index = int((1 - 0.99) * n)
        
        var_95 = sorted_returns[var_95_index] if var_95_index < n else sorted_returns[0]
        var_99 = sorted_returns[var_99_index] if var_99_index < n else sorted_returns[0]
        
        # Expected Shortfall (Conditional VaR)
        tail_losses = sorted_returns[:var_95_index + 1]
        expected_shortfall = sum(tail_losses) / len(tail_losses) if tail_losses else 0
        
        return {
            'var_95': round(var_95, 4),
            'var_99': round(var_99, 4),
            'expected_shortfall': round(expected_shortfall, 4),
            'confidence_level': confidence_level
        }
    
    def validate_risk_limits(self, strategy_config: Dict, user_limits: Dict) -> Dict:
        """
        Validate strategy against user-defined risk limits
        
        Args:
            strategy_config: Strategy configuration with risk parameters
            user_limits: User-defined risk limits
        
        Returns:
            Validation result with recommendations
        """
        violations = []
        warnings = []
        
        # Check maximum loss per trade
        strategy_max_loss = strategy_config.get('max_loss_per_trade', 0)
        user_max_loss = user_limits.get('max_loss_per_trade', float('inf'))
        
        if strategy_max_loss > user_max_loss:
            violations.append({
                'type': 'max_loss_exceeded',
                'message': f'Strategy max loss ({strategy_max_loss}) exceeds user limit ({user_max_loss})',
                'severity': 'high'
            })
        
        # Check position concentration
        position_value = strategy_config.get('position_value', 0)
        account_balance = user_limits.get('account_balance', 1)
        concentration = (position_value / account_balance) * 100
        max_concentration = user_limits.get('max_position_concentration', 25)
        
        if concentration > max_concentration:
            violations.append({
                'type': 'concentration_exceeded',
                'message': f'Position concentration ({concentration:.1f}%) exceeds limit ({max_concentration}%)',
                'severity': 'medium'
            })
        
        # Check number of legs
        num_legs = len(strategy_config.get('legs', []))
        max_legs = user_limits.get('max_legs_per_strategy', 6)
        
        if num_legs > max_legs:
            warnings.append({
                'type': 'too_many_legs',
                'message': f'Strategy has {num_legs} legs, consider simplifying',
                'severity': 'low'
            })
        
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'warnings': warnings,
            'risk_score': self._calculate_risk_score(strategy_config),
            'recommendations': self._generate_risk_recommendations(violations, warnings)
        }
    
    def _norm_cdf(self, x: float) -> float:
        """Standard normal cumulative distribution function"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def _norm_pdf(self, x: float) -> float:
        """Standard normal probability density function"""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
    
    def _find_breakeven_points(self, payoffs: List[Dict]) -> List[float]:
        """Find breakeven points where payoff crosses zero"""
        breakeven_points = []
        
        for i in range(len(payoffs) - 1):
            current_payoff = payoffs[i]['payoff']
            next_payoff = payoffs[i + 1]['payoff']
            
            # Check if payoff crosses zero
            if (current_payoff <= 0 <= next_payoff) or (next_payoff <= 0 <= current_payoff):
                # Linear interpolation to find exact breakeven point
                current_spot = payoffs[i]['spot_price']
                next_spot = payoffs[i + 1]['spot_price']
                
                if next_payoff != current_payoff:
                    breakeven = current_spot - current_payoff * (next_spot - current_spot) / (next_payoff - current_payoff)
                    breakeven_points.append(round(breakeven, 2))
        
        return breakeven_points
    
    def _determine_limiting_factor(self, by_percentage: Decimal, absolute: Decimal, strategy: Decimal) -> str:
        """Determine which risk limit is most restrictive"""
        min_value = min(by_percentage, absolute, strategy)
        
        if min_value == by_percentage:
            return "percentage_based"
        elif min_value == absolute:
            return "absolute_limit"
        else:
            return "strategy_limit"
    
    def _calculate_risk_score(self, strategy_config: Dict) -> float:
        """Calculate overall risk score for strategy (0-100)"""
        # Simplified risk scoring based on strategy characteristics
        base_score = 20  # Base risk for any options strategy
        
        # Add risk for each leg
        num_legs = len(strategy_config.get('legs', []))
        base_score += num_legs * 5
        
        # Add risk for selling options
        selling_legs = sum(1 for leg in strategy_config.get('legs', []) 
                          if leg.get('transaction_type', '').upper() == 'SELL')
        base_score += selling_legs * 15
        
        # Add risk based on time to expiry
        dte = strategy_config.get('days_to_expiry', 30)
        if dte < 7:
            base_score += 20
        elif dte < 15:
            base_score += 10
        
        return min(100, base_score)
    
    def _generate_risk_recommendations(self, violations: List, warnings: List) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if violations:
            recommendations.append("Reduce position size to comply with risk limits")
            recommendations.append("Consider using stop-loss orders")
        
        if warnings:
            recommendations.append("Monitor position closely due to complexity")
            recommendations.append("Consider profit booking at 50% of maximum profit")
        
        if not violations and not warnings:
            recommendations.append("Strategy appears to be within acceptable risk parameters")
        
        return recommendations


# Convenience functions
def calculate_black_scholes_price(spot: float, strike: float, days_to_expiry: int, 
                                 volatility: float, option_type: str = 'call') -> float:
    """Quick Black-Scholes calculation"""
    calculator = RiskCalculator()
    time_to_expiry = days_to_expiry / 365.0
    
    if option_type.lower() == 'call':
        return calculator.black_scholes_call(spot, strike, time_to_expiry, volatility)
    else:
        return calculator.black_scholes_put(spot, strike, time_to_expiry, volatility)


def get_option_greeks(spot: float, strike: float, days_to_expiry: int, 
                     volatility: float, option_type: str = 'call') -> OptionGreeks:
    """Quick Greeks calculation"""
    calculator = RiskCalculator()
    time_to_expiry = days_to_expiry / 365.0
    
    return calculator.calculate_greeks(spot, strike, time_to_expiry, volatility, option_type)