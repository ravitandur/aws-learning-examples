"""
OAuth Factory for Broker Routing
Implements factory pattern to route OAuth requests to appropriate broker handlers
"""

import json
from typing import Dict, Optional, Type
from base_broker_oauth_handler import BaseBrokerOAuthHandler
from broker_configs import get_supported_brokers, supports_oauth

# Import shared logger
try:
    from shared_utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class OAuthFactory:
    """
    Factory class for creating and managing broker OAuth handlers
    Uses strategy pattern to route requests to appropriate implementations
    """
    
    def __init__(self):
        """Initialize the OAuth factory with registered handlers"""
        self._handlers: Dict[str, BaseBrokerOAuthHandler] = {}
        self._handler_classes: Dict[str, Type[BaseBrokerOAuthHandler]] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register all available broker handlers"""
        
        # Register Zerodha handler
        try:
            from handlers.zerodha_oauth_strategy import ZerodhaOAuthStrategy
            self._handler_classes['zerodha'] = ZerodhaOAuthStrategy
            logger.info("Registered Zerodha OAuth handler")
        except ImportError as e:
            logger.warning(f"Failed to register Zerodha handler: {e}")
        
        # Register Angel One handler (when implemented)
        try:
            from handlers.angel_oauth_strategy import AngelOAuthStrategy
            self._handler_classes['angel'] = AngelOAuthStrategy
            logger.info("Registered Angel One OAuth handler")
        except ImportError:
            logger.debug("Angel One OAuth handler not available")
        
        # Register Finvasia handler (when implemented)
        try:
            from handlers.finvasia_oauth_strategy import FinvasiaOAuthStrategy
            self._handler_classes['finvasia'] = FinvasiaOAuthStrategy
            logger.info("Registered Finvasia OAuth handler")
        except ImportError:
            logger.debug("Finvasia OAuth handler not available")
        
        # Register Zebu handler (when implemented)
        try:
            from handlers.zebu_oauth_strategy import ZebuOAuthStrategy
            self._handler_classes['zebu'] = ZebuOAuthStrategy
            logger.info("Registered Zebu OAuth handler")
        except ImportError:
            logger.debug("Zebu OAuth handler not available")
        
        # Register Upstox handler (when implemented)
        try:
            from handlers.upstox_oauth_strategy import UpstoxOAuthStrategy
            self._handler_classes['upstox'] = UpstoxOAuthStrategy
            logger.info("Registered Upstox OAuth handler")
        except ImportError:
            logger.debug("Upstox OAuth handler not available")
    
    def get_handler(self, broker_name: str) -> Optional[BaseBrokerOAuthHandler]:
        """
        Get OAuth handler for specified broker
        
        Args:
            broker_name: Name of the broker
            
        Returns:
            BaseBrokerOAuthHandler instance or None if not supported
        """
        broker_name = broker_name.lower()
        
        # Check if broker is supported
        if not supports_oauth(broker_name):
            logger.warning(f"OAuth not supported for broker: {broker_name}")
            return None
        
        # Return cached handler if exists
        if broker_name in self._handlers:
            return self._handlers[broker_name]
        
        # Create new handler instance
        handler_class = self._handler_classes.get(broker_name)
        if not handler_class:
            logger.error(f"No handler class registered for broker: {broker_name}")
            return None
        
        try:
            # Create and cache handler instance
            handler = handler_class()
            self._handlers[broker_name] = handler
            
            logger.info(f"Created OAuth handler for broker: {broker_name}")
            return handler
            
        except Exception as e:
            logger.error(f"Failed to create handler for {broker_name}: {e}")
            return None
    
    def is_broker_supported(self, broker_name: str) -> bool:
        """
        Check if broker OAuth is supported
        
        Args:
            broker_name: Name of the broker
            
        Returns:
            True if supported, False otherwise
        """
        broker_name = broker_name.lower()
        return broker_name in self._handler_classes and supports_oauth(broker_name)
    
    def get_supported_brokers(self) -> list:
        """
        Get list of brokers with available OAuth handlers
        
        Returns:
            List of supported broker names
        """
        return list(self._handler_classes.keys())
    
    def get_broker_capabilities(self, broker_name: str) -> Dict[str, bool]:
        """
        Get OAuth capabilities for a broker
        
        Args:
            broker_name: Name of the broker
            
        Returns:
            Dictionary of capabilities
        """
        from broker_configs import get_broker_capabilities
        return get_broker_capabilities(broker_name)
    
    def handle_oauth_login(self, broker_name: str, user_id: str, client_id: str) -> Dict[str, any]:
        """
        Handle OAuth login initiation for any broker
        
        Args:
            broker_name: Name of the broker
            user_id: User ID from JWT token
            client_id: Client ID from path parameters
            
        Returns:
            HTTP response dict
        """
        handler = self.get_handler(broker_name)
        if not handler:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Broker not supported',
                    'message': f'OAuth is not supported for broker: {broker_name}'
                })
            }
        
        return handler.handle_oauth_login(user_id, client_id)
    
    def handle_oauth_callback(self, broker_name: str, user_id: str, client_id: str, 
                            callback_params: Dict[str, any]) -> Dict[str, any]:
        """
        Handle OAuth callback for any broker
        
        Args:
            broker_name: Name of the broker
            user_id: User ID from JWT token
            client_id: Client ID from path parameters
            callback_params: Parameters from callback request
            
        Returns:
            HTTP response dict
        """
        handler = self.get_handler(broker_name)
        if not handler:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Broker not supported',
                    'message': f'OAuth is not supported for broker: {broker_name}'
                })
            }
        
        return handler.handle_oauth_callback(user_id, client_id, callback_params)
    
    def handle_oauth_status(self, broker_name: str, user_id: str, client_id: str) -> Dict[str, any]:
        """
        Handle OAuth status check for any broker

        Args:
            broker_name: Name of the broker
            user_id: User ID from JWT token
            client_id: Client ID from path parameters

        Returns:
            HTTP response dict
        """
        handler = self.get_handler(broker_name)
        if not handler:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Broker not supported',
                    'message': f'OAuth is not supported for broker: {broker_name}'
                })
            }

        return handler.handle_oauth_status(user_id, client_id)

    def handle_oauth_refresh(self, broker_name: str, user_id: str, client_id: str) -> Dict[str, any]:
        """
        Handle OAuth token refresh for brokers that support it

        Args:
            broker_name: Name of the broker
            user_id: User ID from JWT token
            client_id: Client ID from path parameters

        Returns:
            HTTP response dict
        """
        handler = self.get_handler(broker_name)
        if not handler:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Broker not supported',
                    'message': f'OAuth is not supported for broker: {broker_name}'
                })
            }

        return handler.handle_oauth_refresh(user_id, client_id)

    def handle_broker_detection(self, user_id: str, client_id: str) -> Dict[str, any]:
        """
        Auto-detect broker from existing broker account and route accordingly
        
        Args:
            user_id: User ID from JWT token
            client_id: Client ID from path parameters
            
        Returns:
            HTTP response dict
        """
        import boto3
        import os
        
        try:
            # Get broker account to determine broker type
            dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
            table = dynamodb.Table(os.environ['BROKER_ACCOUNTS_TABLE'])
            
            response = table.get_item(
                Key={
                    'user_id': user_id,
                    'client_id': client_id
                }
            )
            
            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Broker account not found',
                        'message': f'No broker account found with client_id: {client_id}'
                    })
                }
            
            broker_name = response['Item']['broker_name']
            
            # Check if broker supports OAuth
            if not self.is_broker_supported(broker_name):
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'OAuth not supported',
                        'message': f'OAuth is not currently supported for {broker_name}'
                    })
                }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'data': {
                        'broker_name': broker_name,
                        'supports_oauth': True,
                        'capabilities': self.get_broker_capabilities(broker_name)
                    },
                    'message': f'Broker {broker_name} supports OAuth'
                })
            }
            
        except Exception as e:
            logger.error(f"Error in broker detection: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Internal server error',
                    'message': str(e)
                })
            }

# Global factory instance (singleton pattern)
_oauth_factory = None

def get_oauth_factory() -> OAuthFactory:
    """
    Get singleton OAuth factory instance
    
    Returns:
        OAuthFactory instance
    """
    global _oauth_factory
    
    if _oauth_factory is None:
        _oauth_factory = OAuthFactory()
        logger.info("Created OAuth factory instance")
    
    return _oauth_factory

def route_oauth_request(broker_name: str, action: str, user_id: str, client_id: str, 
                       callback_params: Dict[str, any] = None) -> Dict[str, any]:
    """
    Route OAuth request to appropriate broker handler
    
    Args:
        broker_name: Name of the broker
        action: OAuth action (login, callback, status)
        user_id: User ID from JWT token
        client_id: Client ID from path parameters
        callback_params: Parameters for callback action
        
    Returns:
        HTTP response dict
    """
    factory = get_oauth_factory()
    
    if action == 'login':
        return factory.handle_oauth_login(broker_name, user_id, client_id)
    elif action == 'callback':
        return factory.handle_oauth_callback(broker_name, user_id, client_id, callback_params or {})
    elif action == 'status':
        return factory.handle_oauth_status(broker_name, user_id, client_id)
    elif action == 'refresh':
        return factory.handle_oauth_refresh(broker_name, user_id, client_id)
    else:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid OAuth action',
                'message': f'OAuth action {action} is not supported'
            })
        }