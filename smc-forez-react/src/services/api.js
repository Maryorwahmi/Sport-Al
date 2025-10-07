/**
 * API Service for SMC Forez Trading System
 * Connects to the Python backend server
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * System API
 */
export const systemAPI = {
  // Get system status
  getStatus: async () => {
    const response = await api.get('/api/system/status');
    return response.data;
  },

  // Start trading system
  start: async () => {
    const response = await api.post('/api/system/start');
    return response.data;
  },

  // Stop trading system
  stop: async () => {
    const response = await api.post('/api/system/stop');
    return response.data;
  },
};

/**
 * Account API
 */
export const accountAPI = {
  // Get account information
  getInfo: async () => {
    const response = await api.get('/api/account/info');
    return response.data;
  },
};

/**
 * Signals API
 */
export const signalsAPI = {
  // Get recent signals
  getRecent: async (limit = 10) => {
    const response = await api.get(`/api/signals/recent?limit=${limit}`);
    return response.data;
  },
};

/**
 * Positions API
 */
export const positionsAPI = {
  // Get open positions
  getOpen: async () => {
    const response = await api.get('/api/positions/open');
    return response.data;
  },
};

/**
 * WebSocket connection for real-time updates
 */
export class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.listeners = new Map();
  }

  connect() {
    const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws';
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.notifyListeners(data.type, data.data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect();
    };
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      setTimeout(() => this.connect(), this.reconnectDelay);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  addListener(type, callback) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type).push(callback);
  }

  removeListener(type, callback) {
    if (this.listeners.has(type)) {
      const callbacks = this.listeners.get(type);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  notifyListeners(type, data) {
    if (this.listeners.has(type)) {
      this.listeners.get(type).forEach((callback) => callback(data));
    }
  }

  send(type, data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    }
  }
}

// Export singleton instance
export const wsService = new WebSocketService();

export default api;
