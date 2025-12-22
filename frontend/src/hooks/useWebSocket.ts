/**
 * WebSocket Hook
 * Provides real-time connection management for trading updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  channel?: string;
  data?: any;
  timestamp?: number;
}

// Connection states
export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting';

// Subscription channels
export type SubscriptionChannel = 'orders' | 'positions' | 'pnl' | 'executions' | 'all';

// Hook options
export interface UseWebSocketOptions {
  autoConnect?: boolean;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

// Hook return type
export interface UseWebSocketReturn {
  connectionState: ConnectionState;
  isConnected: boolean;
  subscriptions: SubscriptionChannel[];
  connect: () => void;
  disconnect: () => void;
  subscribe: (channels: SubscriptionChannel | SubscriptionChannel[]) => void;
  unsubscribe: (channels: SubscriptionChannel | SubscriptionChannel[]) => void;
  sendMessage: (message: any) => void;
  lastMessage: WebSocketMessage | null;
}

// Default WebSocket URL from environment
const getWebSocketUrl = (): string => {
  const env = process.env.REACT_APP_ENVIRONMENT || 'dev';
  const wsUrl = process.env[`REACT_APP_WS_URL_${env.toUpperCase()}`] ||
    process.env.REACT_APP_WS_URL ||
    '';
  return wsUrl;
};

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    autoConnect = true,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const { tokens, isAuthenticated } = useAuth();

  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [subscriptions, setSubscriptions] = useState<SubscriptionChannel[]>([]);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null; // Prevent reconnect on intentional close
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    if (!isAuthenticated || !tokens?.idToken) {
      console.warn('WebSocket: Cannot connect - not authenticated');
      return;
    }

    const wsUrl = getWebSocketUrl();
    if (!wsUrl) {
      console.warn('WebSocket: No URL configured');
      return;
    }

    // Build URL with token
    const urlWithToken = `${wsUrl}?token=${encodeURIComponent(tokens.idToken)}`;

    setConnectionState('connecting');

    try {
      const ws = new WebSocket(urlWithToken);

      ws.onopen = () => {
        console.log('WebSocket: Connected');
        setConnectionState('connected');
        reconnectAttemptsRef.current = 0;
        onConnect?.();

        // Re-subscribe to previous subscriptions
        if (subscriptions.length > 0) {
          ws.send(JSON.stringify({
            action: 'subscribe',
            channels: subscriptions,
          }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Handle subscription confirmations
          if (message.type === 'subscribed') {
            setSubscriptions(message.data?.channels || []);
          } else if (message.type === 'unsubscribed') {
            setSubscriptions(message.data?.channels || []);
          }

          onMessage?.(message);
        } catch (e) {
          console.error('WebSocket: Failed to parse message', e);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket: Disconnected');
        setConnectionState('disconnected');
        wsRef.current = null;
        onDisconnect?.();

        // Attempt reconnection
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          setConnectionState('reconnecting');
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            console.log(`WebSocket: Reconnect attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`);
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket: Error', error);
        onError?.(error);
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('WebSocket: Failed to connect', e);
      setConnectionState('disconnected');
    }
  }, [
    isAuthenticated,
    tokens,
    subscriptions,
    autoReconnect,
    reconnectInterval,
    maxReconnectAttempts,
    onConnect,
    onDisconnect,
    onMessage,
    onError,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    cleanup();
    setConnectionState('disconnected');
    reconnectAttemptsRef.current = maxReconnectAttempts; // Prevent auto-reconnect
  }, [cleanup, maxReconnectAttempts]);

  // Subscribe to channels
  const subscribe = useCallback((channels: SubscriptionChannel | SubscriptionChannel[]) => {
    const channelArray = Array.isArray(channels) ? channels : [channels];

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        channels: channelArray,
      }));
    }

    // Optimistically update local state
    setSubscriptions((prev) => {
      const newSubs = new Set([...prev, ...channelArray]);
      return Array.from(newSubs) as SubscriptionChannel[];
    });
  }, []);

  // Unsubscribe from channels
  const unsubscribe = useCallback((channels: SubscriptionChannel | SubscriptionChannel[]) => {
    const channelArray = Array.isArray(channels) ? channels : [channels];

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        channels: channelArray,
      }));
    }

    // Optimistically update local state
    setSubscriptions((prev) => prev.filter((ch) => !channelArray.includes(ch)));
  }, []);

  // Send raw message
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket: Cannot send message - not connected');
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && isAuthenticated) {
      connect();
    }

    return () => {
      cleanup();
    };
  }, [autoConnect, isAuthenticated, connect, cleanup]);

  // Reconnect when authentication changes
  useEffect(() => {
    if (isAuthenticated && connectionState === 'disconnected' && autoConnect) {
      reconnectAttemptsRef.current = 0;
      connect();
    } else if (!isAuthenticated) {
      disconnect();
    }
  }, [isAuthenticated, connectionState, autoConnect, connect, disconnect]);

  return {
    connectionState,
    isConnected: connectionState === 'connected',
    subscriptions,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    sendMessage,
    lastMessage,
  };
}

export default useWebSocket;
