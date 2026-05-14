import { useEffect, useState } from 'react';
import type { LiveUpdateMessage } from '@/src/types';

const DEFAULT_WS_URL = 'ws://localhost:8000/ws/live';
const WS_URL = import.meta.env.VITE_WS_URL ?? DEFAULT_WS_URL;

interface WebSocketState {
  isConnected: boolean;
  lastMessage: LiveUpdateMessage | null;
  error: string | null;
}

function isLiveUpdateMessage(value: unknown): value is LiveUpdateMessage {
  if (!value || typeof value !== 'object') return false;
  const message = value as Partial<LiveUpdateMessage>;
  return message.type === 'live_update' && Array.isArray(message.provinces);
}

export function useWebSocket(url = WS_URL): WebSocketState {
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    lastMessage: null,
    error: null,
  });

  useEffect(() => {
    let socket: WebSocket | null = null;
    let closedByEffect = false;
    let retryDelay = 1000;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      socket = new WebSocket(url);

      socket.onopen = () => {
        retryDelay = 1000;
        setState((current) => ({ ...current, isConnected: true, error: null }));
      };

      socket.onmessage = (event) => {
        try {
          const payload: unknown = JSON.parse(String(event.data));
          if (isLiveUpdateMessage(payload)) {
            setState({ isConnected: true, lastMessage: payload, error: null });
          }
        } catch (error) {
          setState((current) => ({
            ...current,
            error: error instanceof Error ? error.message : 'Invalid websocket payload',
          }));
        }
      };

      socket.onerror = () => {
        setState((current) => ({
          ...current,
          isConnected: false,
          error: 'Realtime connection unavailable',
        }));
      };

      socket.onclose = () => {
        setState((current) => ({ ...current, isConnected: false }));
        if (!closedByEffect) {
          retryTimer = setTimeout(connect, retryDelay);
          retryDelay = Math.min(retryDelay * 2, 30000);
        }
      };
    };

    connect();

    return () => {
      closedByEffect = true;
      if (retryTimer) clearTimeout(retryTimer);
      socket?.close();
    };
  }, [url]);

  return state;
}
