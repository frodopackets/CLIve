import { WebSocketMessage, ConnectionStatus } from '../types';

export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  getAccessToken?: () => Promise<string | null>;
}

export interface WebSocketCallbacks {
  onMessage?: (message: WebSocketMessage) => void;
  onConnectionChange?: (status: ConnectionStatus) => void;
  onError?: (error: Event) => void;
  onStreamChunk?: (chunk: string) => void;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private callbacks: WebSocketCallbacks;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private connectionStatus: ConnectionStatus = 'disconnected';
  private isManualClose = false;

  constructor(config: WebSocketConfig, callbacks: WebSocketCallbacks = {}) {
    this.config = {
      url: config.url,
      reconnectInterval: config.reconnectInterval || 3000,
      maxReconnectAttempts: config.maxReconnectAttempts || 5,
      heartbeatInterval: config.heartbeatInterval || 30000,
      getAccessToken: config.getAccessToken,
    } as Required<WebSocketConfig>;
    this.callbacks = callbacks;
  }

  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.isManualClose = false;
    this.setConnectionStatus('connecting');

    try {
      let wsUrl = this.config.url;
      
      // Add authentication token to WebSocket URL if available
      if (this.config.getAccessToken) {
        const token = await this.config.getAccessToken();
        if (token) {
          const separator = wsUrl.includes('?') ? '&' : '?';
          wsUrl = `${wsUrl}${separator}token=${encodeURIComponent(token)}`;
        }
      }

      this.ws = new WebSocket(wsUrl);
      this.setupEventListeners();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.handleConnectionError();
    }
  }

  disconnect(): void {
    this.isManualClose = true;
    this.cleanup();
    this.setConnectionStatus('disconnected');
  }

  sendMessage(message: WebSocketMessage): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Failed to send message:', error);
        return false;
      }
    }
    return false;
  }

  getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus;
  }

  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.setConnectionStatus('connected');
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle streaming responses
        if (data.type === 'stream' && this.callbacks.onStreamChunk) {
          this.callbacks.onStreamChunk(data.content);
          return;
        }

        // Handle regular messages
        if (this.callbacks.onMessage) {
          this.callbacks.onMessage(data as WebSocketMessage);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.cleanup();
      
      if (!this.isManualClose) {
        this.setConnectionStatus('disconnected');
        this.attemptReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (this.callbacks.onError) {
        this.callbacks.onError(error);
      }
      this.handleConnectionError();
    };
  }

  private setConnectionStatus(status: ConnectionStatus): void {
    if (this.connectionStatus !== status) {
      this.connectionStatus = status;
      if (this.callbacks.onConnectionChange) {
        this.callbacks.onConnectionChange(status);
      }
    }
  }

  private handleConnectionError(): void {
    this.cleanup();
    if (!this.isManualClose) {
      this.setConnectionStatus('disconnected');
      this.attemptReconnect();
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})...`);

    this.reconnectTimer = setTimeout(async () => {
      await this.connect();
    }, this.config.reconnectInterval);
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.sendMessage({
          type: 'status',
          content: 'ping',
          sessionId: '',
          timestamp: new Date().toISOString(),
        });
      }
    }, this.config.heartbeatInterval);
  }

  private cleanup(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close();
      }
      
      this.ws = null;
    }
  }
}