// src/utils/socket.ts
import { io, Socket } from 'socket.io-client';

class SocketManager {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;

  // Event listeners storage
  private eventListeners = new Map<string, Function[]>();

  constructor() {
    this.initSocket();
  }

  private initSocket() {
    if (this.socket?.connected || this.isConnecting) return;

    this.isConnecting = true;

    try {
      // Use relative '/' path to allow LAN origin and Vite's /socket.io proxies
      this.socket = io('/', {
        transports: ['websocket', 'polling'],
        timeout: 20000,
        forceNew: true,
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
        reconnectionDelayMax: 5000,
        randomizationFactor: 0.5,
        withCredentials: true, // Enable credentials for CORS requests
        auth: {
          token: localStorage.getItem('dashboard_auth_token') || undefined,
        },
      });

      this.setupSocketListeners();
    } catch (error) {
      console.error('Failed to initialize socket:', error);
      this.isConnecting = false;
    }
  }

  private setupSocketListeners() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('Socket.IO connected');
      this.reconnectAttempts = 0;
      this.isConnecting = false;
      this.emitToListeners('connect');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('Socket.IO disconnected:', reason);
      this.isConnecting = false;
      this.emitToListeners('disconnect', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('Socket.IO connection error:', error);
      this.isConnecting = false;
      this.reconnectAttempts++;
      this.emitToListeners('connect_error', error);
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('Socket.IO reconnected after', attemptNumber, 'attemptNumber');
      this.reconnectAttempts = 0;
      this.isConnecting = false;
      this.emitToListeners('reconnect', attemptNumber);
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('Socket.IO reconnection failed:', error);
      this.isConnecting = false;
      this.emitToListeners('reconnect_error', error);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('Socket.IO failed to reconnect after max attempts');
      this.isConnecting = false;
      this.emitToListeners('reconnect_failed');
    });

    // Proxy all incoming events to our internal listeners
    this.socket.onAny((eventName, ...args) => {
      this.emitToListeners(eventName, ...args);
    });
  }


  // Public methods
  getSocket(): Socket | null {
    return this.socket;
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  connect() {
    if (!this.socket) {
      this.initSocket();
    } else if (!this.socket.connected && !this.isConnecting) {
      this.isConnecting = true;
      this.socket.connect();
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
    }
  }

  // Event listener management
  on(event: string, callback: Function) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(callback);
  }

  off(event: string, callback?: Function) {
    if (!this.eventListeners.has(event)) return;

    const listeners = this.eventListeners.get(event)!;
    if (callback) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    } else {
      this.eventListeners.delete(event);
    }
  }

  private emitToListeners(event: string, ...args: any[]) {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(...args);
        } catch (error) {
          console.error('Error in event listener for', event, ':', error);
        }
      });
    }
  }

  // Emit events to server
  emit(event: string, ...args: any[]) {
    if (this.socket?.connected) {
      this.socket.emit(event, ...args);
    } else {
      console.warn('Socket not connected, cannot emit:', event);
    }
  }
}

// Export singleton instance
const socketManager = new SocketManager();

export default socketManager;
export { SocketManager };