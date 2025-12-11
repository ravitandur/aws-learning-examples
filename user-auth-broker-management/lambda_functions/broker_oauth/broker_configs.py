"""
Centralized Broker OAuth Configuration System
Contains broker-specific OAuth settings and capabilities
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from enum import Enum

class OAuthFlow(Enum):
    """Supported OAuth flow types"""
    POPUP = "popup"
    REDIRECT = "redirect"
    EMBEDDED = "embedded"

class TokenType(Enum):
    """Token types supported by brokers"""
    SESSION = "session"          # Daily session tokens (Zerodha)
    BEARER = "bearer"           # Standard OAuth bearer tokens
    API_KEY = "api_key"         # API key based authentication

class ExpiryPattern(Enum):
    """Token expiry patterns"""
    DAILY = "daily"             # Expires daily (Zerodha - 6 AM IST)
    REFRESH = "refresh"         # Refreshable tokens (Angel One)
    LONG_LIVED = "long_lived"   # Long-lived tokens (weeks/months)

@dataclass
class BrokerOAuthConfig:
    """Configuration for broker OAuth implementation"""
    
    # Basic broker info
    broker_name: str
    display_name: str
    
    # OAuth configuration
    oauth_flow: OAuthFlow
    token_type: TokenType
    expiry_pattern: ExpiryPattern
    
    # URLs and endpoints
    oauth_base_url: str
    token_exchange_url: Optional[str] = None
    
    # OAuth parameters
    requires_daily_auth: bool = False
    supports_refresh: bool = False
    supports_revoke: bool = False
    
    # Token expiry specifics
    token_validity_hours: Optional[int] = None  # For session tokens
    daily_expiry_time: Optional[str] = None     # For daily expiry (e.g., "06:00:00")
    timezone: Optional[str] = None              # For daily expiry
    
    # API validation patterns
    api_key_pattern: Optional[str] = None
    api_secret_pattern: Optional[str] = None
    client_id_pattern: Optional[str] = None
    
    # Popup dimensions (for frontend)
    popup_width: int = 500
    popup_height: int = 600

# Broker configurations
BROKER_CONFIGS: Dict[str, BrokerOAuthConfig] = {
    
    # Zerodha Kite Connect
    'zerodha': BrokerOAuthConfig(
        broker_name='zerodha',
        display_name='Zerodha Kite',
        oauth_flow=OAuthFlow.POPUP,
        token_type=TokenType.SESSION,
        expiry_pattern=ExpiryPattern.DAILY,
        oauth_base_url='https://kite.zerodha.com/connect/login',
        token_exchange_url='https://api.kite.trade/session/token',
        requires_daily_auth=True,
        supports_refresh=False,
        supports_revoke=False,
        token_validity_hours=18,  # 6 AM to 6 AM next day
        daily_expiry_time='06:00:00',
        timezone='Asia/Kolkata',
        api_key_pattern=r'^[a-zA-Z0-9]{16}$',  # 16 character alphanumeric
        api_secret_pattern=r'^[a-zA-Z0-9]{32}$',  # 32 character alphanumeric
        popup_width=600,
        popup_height=700
    ),
    
    # Angel One SmartAPI
    'angel': BrokerOAuthConfig(
        broker_name='angel',
        display_name='Angel One',
        oauth_flow=OAuthFlow.POPUP,
        token_type=TokenType.BEARER,
        expiry_pattern=ExpiryPattern.REFRESH,
        oauth_base_url='https://smartapi.angelbroking.com/publisher-login',
        token_exchange_url='https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword',
        requires_daily_auth=False,
        supports_refresh=True,
        supports_revoke=True,
        token_validity_hours=24,
        api_key_pattern=r'^[A-Z0-9]{8}$',  # 8 character uppercase alphanumeric
        api_secret_pattern=r'^[A-Za-z0-9@#$%^&*]{16,}$',  # 16+ characters
        client_id_pattern=r'^[A-Z]{1}[0-9]{6}$',  # Format: A123456
        popup_width=500,
        popup_height=650
    ),
    
    # Finvasia Shoonya
    'finvasia': BrokerOAuthConfig(
        broker_name='finvasia',
        display_name='Finvasia Shoonya',
        oauth_flow=OAuthFlow.POPUP,
        token_type=TokenType.SESSION,
        expiry_pattern=ExpiryPattern.DAILY,
        oauth_base_url='https://shoonya.finvasia.com/NorenWClientTP/',
        requires_daily_auth=True,
        supports_refresh=False,
        supports_revoke=False,
        token_validity_hours=18,
        daily_expiry_time='06:00:00',
        timezone='Asia/Kolkata',
        api_key_pattern=r'^[a-zA-Z0-9]{10,}$',
        api_secret_pattern=r'^[a-zA-Z0-9]{20,}$',
        popup_width=550,
        popup_height=650
    ),
    
    # Zebu MYNT API
    'zebu': BrokerOAuthConfig(
        broker_name='zebu',
        display_name='Zebu MYNT',
        oauth_flow=OAuthFlow.POPUP,
        token_type=TokenType.BEARER,
        expiry_pattern=ExpiryPattern.REFRESH,
        oauth_base_url='https://go.mynt.in/OAuthlogin/authorize/oauth',
        token_exchange_url='https://go.mynt.in/NorenWClientAPI/GenAcsTok',
        requires_daily_auth=False,
        supports_refresh=True,
        supports_revoke=False,
        token_validity_hours=1,  # Access token expires in ~1 hour (3600 seconds)
        daily_expiry_time=None,
        timezone='Asia/Kolkata',
        api_key_pattern=r'^[a-zA-Z0-9_-]{10,50}$',  # Vendor code pattern
        api_secret_pattern=r'^[a-zA-Z0-9_-]{10,100}$',  # App key pattern
        popup_width=500,
        popup_height=650
    ),
    
    # Upstox
    'upstox': BrokerOAuthConfig(
        broker_name='upstox',
        display_name='Upstox',
        oauth_flow=OAuthFlow.POPUP,
        token_type=TokenType.BEARER,
        expiry_pattern=ExpiryPattern.REFRESH,
        oauth_base_url='https://api.upstox.com/v2/login/authorization/dialog',
        token_exchange_url='https://api.upstox.com/v2/login/authorization/token',
        requires_daily_auth=False,
        supports_refresh=True,
        supports_revoke=True,
        token_validity_hours=24,
        api_key_pattern=r'^[a-z0-9-]{36}$',  # UUID format
        api_secret_pattern=r'^[a-zA-Z0-9]{40}$',
        popup_width=500,
        popup_height=600
    )
}

def get_broker_config(broker_name: str) -> Optional[BrokerOAuthConfig]:
    """
    Get configuration for a specific broker
    
    Args:
        broker_name: Name of the broker
        
    Returns:
        BrokerOAuthConfig if found, None otherwise
    """
    return BROKER_CONFIGS.get(broker_name.lower())

def get_supported_brokers() -> List[str]:
    """
    Get list of all supported broker names
    
    Returns:
        List of broker names
    """
    return list(BROKER_CONFIGS.keys())

def supports_oauth(broker_name: str) -> bool:
    """
    Check if broker supports OAuth
    
    Args:
        broker_name: Name of the broker
        
    Returns:
        True if OAuth is supported, False otherwise
    """
    config = get_broker_config(broker_name)
    return config is not None

def requires_daily_auth(broker_name: str) -> bool:
    """
    Check if broker requires daily authentication
    
    Args:
        broker_name: Name of the broker
        
    Returns:
        True if daily auth is required, False otherwise
    """
    config = get_broker_config(broker_name)
    return config.requires_daily_auth if config else False

def supports_token_refresh(broker_name: str) -> bool:
    """
    Check if broker supports token refresh
    
    Args:
        broker_name: Name of the broker
        
    Returns:
        True if token refresh is supported, False otherwise
    """
    config = get_broker_config(broker_name)
    return config.supports_refresh if config else False

def get_popup_dimensions(broker_name: str) -> tuple:
    """
    Get popup dimensions for broker
    
    Args:
        broker_name: Name of the broker
        
    Returns:
        Tuple of (width, height)
    """
    config = get_broker_config(broker_name)
    if config:
        return (config.popup_width, config.popup_height)
    return (500, 600)  # Default dimensions

def validate_api_credentials(broker_name: str, api_key: str, api_secret: str) -> tuple:
    """
    Validate API credentials format for broker
    
    Args:
        broker_name: Name of the broker
        api_key: API key to validate
        api_secret: API secret to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    import re
    
    config = get_broker_config(broker_name)
    if not config:
        return False, f"Broker {broker_name} is not supported"
    
    # Validate API key pattern
    if config.api_key_pattern:
        if not re.match(config.api_key_pattern, api_key):
            return False, f"Invalid API key format for {config.display_name}"
    
    # Validate API secret pattern
    if config.api_secret_pattern:
        if not re.match(config.api_secret_pattern, api_secret):
            return False, f"Invalid API secret format for {config.display_name}"
    
    return True, None

def validate_client_id(broker_name: str, client_id: str) -> tuple:
    """
    Validate client ID format for broker
    
    Args:
        broker_name: Name of the broker
        client_id: Client ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    import re
    
    config = get_broker_config(broker_name)
    if not config:
        return False, f"Broker {broker_name} is not supported"
    
    # Validate client ID pattern if specified
    if config.client_id_pattern:
        if not re.match(config.client_id_pattern, client_id):
            return False, f"Invalid client ID format for {config.display_name}"
    
    return True, None

def get_broker_capabilities(broker_name: str) -> Dict[str, bool]:
    """
    Get OAuth capabilities for a broker
    
    Args:
        broker_name: Name of the broker
        
    Returns:
        Dictionary of capabilities
    """
    config = get_broker_config(broker_name)
    if not config:
        return {}
    
    return {
        'supports_oauth': True,
        'requires_daily_auth': config.requires_daily_auth,
        'supports_refresh': config.supports_refresh,
        'supports_revoke': config.supports_revoke,
        'oauth_flow': config.oauth_flow.value,
        'token_type': config.token_type.value,
        'expiry_pattern': config.expiry_pattern.value
    }