"""
Indian Market Utilities
Shared utilities for Indian stock market operations, timings, and configurations
"""

import pytz
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
import json


# Indian Market Configuration
INDIAN_MARKET_CONFIG = {
    "timezone": "Asia/Kolkata",
    "trading_session": {
        "pre_market": {"start": "09:00", "end": "09:15"},
        "regular": {"start": "09:15", "end": "15:30"},
        "post_market": {"start": "15:40", "end": "16:00"}
    },
    "indices": {
        "NIFTY": {
            "lot_size": 25,
            "weekly_expiry": "THURSDAY",
            "monthly_expiry": "LAST_THURSDAY",
            "strike_difference": 50,
            "tick_size": 0.05,
            "exchange": "NSE"
        },
        "BANKNIFTY": {
            "lot_size": 15,
            "weekly_expiry": "WEDNESDAY",
            "monthly_expiry": "LAST_WEDNESDAY",
            "strike_difference": 100,
            "tick_size": 0.05,
            "exchange": "NSE"
        },
        "FINNIFTY": {
            "lot_size": 25,
            "weekly_expiry": "TUESDAY",
            "monthly_expiry": "LAST_TUESDAY",
            "strike_difference": 50,
            "tick_size": 0.05,
            "exchange": "NSE"
        },
        "MIDCPNIFTY": {
            "lot_size": 75,
            "weekly_expiry": "MONDAY",
            "monthly_expiry": "LAST_MONDAY",
            "strike_difference": 25,
            "tick_size": 0.05,
            "exchange": "NSE"
        },
        "SENSEX": {
            "lot_size": 10,
            "weekly_expiry": "FRIDAY",
            "monthly_expiry": "LAST_FRIDAY",
            "strike_difference": 100,
            "tick_size": 1,
            "exchange": "BSE"
        }
    },
    "holidays": [
        # Major Indian market holidays (partial list - should be updated annually)
        "2025-01-26",  # Republic Day
        "2025-03-14",  # Holi
        "2025-04-18",  # Good Friday
        "2025-08-15",  # Independence Day
        "2025-10-02",  # Gandhi Jayanti
        "2025-11-01",  # Diwali (Laxmi Pujan)
        "2025-11-21",  # Guru Nanak Jayanti
    ]
}


class IndianMarketUtils:
    """Utility class for Indian market operations"""
    
    def __init__(self):
        self.ist = pytz.timezone(INDIAN_MARKET_CONFIG["timezone"])
        self.config = INDIAN_MARKET_CONFIG
    
    def get_current_ist_time(self) -> datetime:
        """Get current time in IST"""
        return datetime.now(self.ist)
    
    def is_market_open(self, check_time: Optional[datetime] = None) -> bool:
        """
        Check if market is currently open
        
        Args:
            check_time: Time to check (defaults to current IST time)
        
        Returns:
            bool: True if market is open
        """
        if check_time is None:
            check_time = self.get_current_ist_time()
        
        # Check if it's a weekend
        if check_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check if it's a holiday
        if self.is_market_holiday(check_time.date()):
            return False
        
        # Check trading session times
        current_time = check_time.time()
        session = self.config["trading_session"]["regular"]
        start_time = time.fromisoformat(session["start"])
        end_time = time.fromisoformat(session["end"])
        
        return start_time <= current_time <= end_time
    
    def is_market_holiday(self, check_date) -> bool:
        """Check if given date is a market holiday"""
        date_str = check_date.strftime("%Y-%m-%d")
        return date_str in self.config["holidays"]
    
    def get_next_trading_day(self, from_date: Optional[datetime] = None) -> datetime:
        """
        Get the next trading day from given date
        
        Args:
            from_date: Starting date (defaults to current IST time)
        
        Returns:
            datetime: Next trading day
        """
        if from_date is None:
            from_date = self.get_current_ist_time()
        
        next_day = from_date + timedelta(days=1)
        
        while (next_day.weekday() >= 5 or 
               self.is_market_holiday(next_day.date())):
            next_day += timedelta(days=1)
        
        return next_day
    
    def get_market_session_info(self) -> Dict:
        """Get current market session information"""
        current_time = self.get_current_ist_time()
        current_time_only = current_time.time()
        
        sessions = self.config["trading_session"]
        
        for session_name, session_info in sessions.items():
            start_time = time.fromisoformat(session_info["start"])
            end_time = time.fromisoformat(session_info["end"])
            
            if start_time <= current_time_only <= end_time:
                return {
                    "session": session_name,
                    "is_open": True,
                    "start_time": session_info["start"],
                    "end_time": session_info["end"]
                }
        
        return {
            "session": "closed",
            "is_open": False,
            "next_session": self._get_next_session()
        }
    
    def _get_next_session(self) -> Dict:
        """Get information about the next trading session"""
        current_time = self.get_current_ist_time()
        current_time_only = current_time.time()
        
        sessions = self.config["trading_session"]
        
        # Check if any session starts later today
        for session_name, session_info in sessions.items():
            start_time = time.fromisoformat(session_info["start"])
            if current_time_only < start_time:
                return {
                    "session": session_name,
                    "start_time": session_info["start"],
                    "date": current_time.date().isoformat()
                }
        
        # Next session is tomorrow's pre-market
        next_trading_day = self.get_next_trading_day(current_time)
        return {
            "session": "pre_market",
            "start_time": sessions["pre_market"]["start"],
            "date": next_trading_day.date().isoformat()
        }
    
    def get_index_config(self, symbol: str) -> Optional[Dict]:
        """Get configuration for a specific index"""
        return self.config["indices"].get(symbol.upper())
    
    def get_lot_size(self, symbol: str) -> int:
        """Get lot size for a given symbol"""
        index_config = self.get_index_config(symbol)
        return index_config["lot_size"] if index_config else 1
    
    def get_strike_difference(self, symbol: str) -> float:
        """Get strike difference for a given symbol"""
        index_config = self.get_index_config(symbol)
        return index_config["strike_difference"] if index_config else 50
    
    def calculate_nearest_strike(self, symbol: str, spot_price: float) -> float:
        """Calculate nearest ATM strike for given spot price"""
        strike_diff = self.get_strike_difference(symbol)
        return round(spot_price / strike_diff) * strike_diff
    
    def get_expiry_dates(self, symbol: str, weeks: int = 4) -> List[datetime]:
        """
        Get next N weekly expiry dates for a symbol
        
        Args:
            symbol: Index symbol
            weeks: Number of weeks to get
        
        Returns:
            List of datetime objects representing expiry dates
        """
        index_config = self.get_index_config(symbol)
        if not index_config:
            return []
        
        weekly_expiry_day = index_config["weekly_expiry"]
        day_mapping = {
            "MONDAY": 0,
            "TUESDAY": 1,
            "WEDNESDAY": 2,
            "THURSDAY": 3,
            "FRIDAY": 4
        }
        
        target_weekday = day_mapping.get(weekly_expiry_day, 3)  # Default to Thursday
        expiry_dates = []
        
        current_date = self.get_current_ist_time().date()
        
        for i in range(weeks * 2):  # Check more days to find valid expiries
            check_date = current_date + timedelta(days=i)
            
            if (check_date.weekday() == target_weekday and 
                not self.is_market_holiday(check_date) and
                len(expiry_dates) < weeks):
                expiry_dates.append(
                    datetime.combine(check_date, time(15, 30), tzinfo=self.ist)
                )
        
        return expiry_dates
    
    def is_expiry_day(self, symbol: str, check_date: Optional[datetime] = None) -> bool:
        """Check if given date is an expiry day for the symbol"""
        if check_date is None:
            check_date = self.get_current_ist_time()
        
        expiry_dates = self.get_expiry_dates(symbol, weeks=1)
        return any(exp.date() == check_date.date() for exp in expiry_dates)
    
    def time_to_market_close(self) -> Optional[timedelta]:
        """Get time remaining until market closes"""
        current_time = self.get_current_ist_time()
        
        if not self.is_market_open(current_time):
            return None
        
        market_close = current_time.replace(
            hour=15, minute=30, second=0, microsecond=0
        )
        
        return market_close - current_time
    
    def format_option_symbol(self, underlying: str, expiry: datetime, 
                           strike: float, option_type: str) -> str:
        """
        Format option symbol according to Indian market conventions
        
        Args:
            underlying: Underlying symbol (NIFTY, BANKNIFTY, etc.)
            expiry: Expiry date
            strike: Strike price
            option_type: CE or PE
        
        Returns:
            Formatted option symbol
        """
        # Format: NIFTY25SEP24900CE
        expiry_str = expiry.strftime("%d%b%y").upper()
        strike_str = f"{int(strike)}"
        
        return f"{underlying.upper()}{expiry_str}{strike_str}{option_type.upper()}"
    
    def validate_trading_time(self, entry_time: str, exit_time: str) -> Dict:
        """
        Validate if given entry and exit times are within trading hours
        
        Args:
            entry_time: Entry time in HH:MM format
            exit_time: Exit time in HH:MM format
        
        Returns:
            Dict with validation result and messages
        """
        try:
            entry_time_obj = time.fromisoformat(entry_time)
            exit_time_obj = time.fromisoformat(exit_time)
            
            market_start = time.fromisoformat(
                self.config["trading_session"]["regular"]["start"]
            )
            market_end = time.fromisoformat(
                self.config["trading_session"]["regular"]["end"]
            )
            
            errors = []
            
            if entry_time_obj < market_start or entry_time_obj > market_end:
                errors.append(f"Entry time {entry_time} is outside market hours")
            
            if exit_time_obj < market_start or exit_time_obj > market_end:
                errors.append(f"Exit time {exit_time} is outside market hours")
            
            if entry_time_obj >= exit_time_obj:
                errors.append("Entry time must be before exit time")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "market_hours": {
                    "start": self.config["trading_session"]["regular"]["start"],
                    "end": self.config["trading_session"]["regular"]["end"]
                }
            }
            
        except ValueError as e:
            return {
                "valid": False,
                "errors": [f"Invalid time format: {str(e)}"],
                "market_hours": {
                    "start": self.config["trading_session"]["regular"]["start"],
                    "end": self.config["trading_session"]["regular"]["end"]
                }
            }


# Convenience functions for direct import
def get_indian_market_utils() -> IndianMarketUtils:
    """Get instance of Indian Market Utils"""
    return IndianMarketUtils()


def is_market_open() -> bool:
    """Quick check if market is currently open"""
    return IndianMarketUtils().is_market_open()


def get_current_ist_time() -> datetime:
    """Get current IST time"""
    return IndianMarketUtils().get_current_ist_time()


def get_lot_size(symbol: str) -> int:
    """Get lot size for symbol"""
    return IndianMarketUtils().get_lot_size(symbol)


def get_nearest_strike(symbol: str, spot_price: float) -> float:
    """Get nearest ATM strike"""
    return IndianMarketUtils().calculate_nearest_strike(symbol, spot_price)