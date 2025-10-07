/**
 * API Service for SMC-Forez-H4 Backend
 * Handles all communication with the FastAPI backend server
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Health Check API
 */
export const healthCheck = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Live Signals API
 */
export const signalsAPI = {
  // Get current live signals
  getCurrentSignals: async (symbols = []) => {
    const params = symbols.length > 0 ? { symbols: symbols.join(',') } : {};
    const response = await apiClient.get('/api/signals/current', { params });
    return response.data;
  },

  // Get signal history
  getSignalHistory: async (limit = 50, symbol = null) => {
    const params = { limit };
    if (symbol) params.symbol = symbol;
    const response = await apiClient.get('/api/signals/history', { params });
    return response.data;
  },

  // Get signal by ID
  getSignalById: async (signalId) => {
    const response = await apiClient.get(`/api/signals/${signalId}`);
    return response.data;
  },

  // Analyze symbol for signals
  analyzeSymbol: async (symbol, timeframe = 'H1') => {
    const response = await apiClient.post('/api/signals/analyze', {
      symbol,
      timeframe
    });
    return response.data;
  }
};

/**
 * Backtest API
 */
export const backtestAPI = {
  // Run a new backtest
  runBacktest: async (config) => {
    const response = await apiClient.post('/api/backtest/run', config);
    return response.data;
  },

  // Get backtest results
  getBacktestResults: async (backtestId) => {
    const response = await apiClient.get(`/api/backtest/${backtestId}`);
    return response.data;
  },

  // Get all backtest results
  getAllBacktests: async (limit = 20) => {
    const response = await apiClient.get('/api/backtest/all', { params: { limit } });
    return response.data;
  },

  // Delete backtest
  deleteBacktest: async (backtestId) => {
    const response = await apiClient.delete(`/api/backtest/${backtestId}`);
    return response.data;
  }
};

/**
 * Market Data API
 */
export const marketDataAPI = {
  // Get OHLC data for a symbol
  getOHLCData: async (symbol, timeframe, count = 100) => {
    const response = await apiClient.get('/api/market/ohlc', {
      params: { symbol, timeframe, count }
    });
    return response.data;
  },

  // Get current price
  getCurrentPrice: async (symbol) => {
    const response = await apiClient.get(`/api/market/price/${symbol}`);
    return response.data;
  },

  // Get supported symbols
  getSupportedSymbols: async () => {
    const response = await apiClient.get('/api/market/symbols');
    return response.data;
  }
};

/**
 * Analysis API
 */
export const analysisAPI = {
  // Get multi-timeframe analysis
  getMultiTimeframeAnalysis: async (symbol) => {
    const response = await apiClient.get(`/api/analysis/mtf/${symbol}`);
    return response.data;
  },

  // Get SMC patterns
  getSMCPatterns: async (symbol, timeframe) => {
    const response = await apiClient.get('/api/analysis/smc', {
      params: { symbol, timeframe }
    });
    return response.data;
  },

  // Get market structure
  getMarketStructure: async (symbol, timeframe) => {
    const response = await apiClient.get('/api/analysis/structure', {
      params: { symbol, timeframe }
    });
    return response.data;
  }
};

/**
 * Settings API
 */
export const settingsAPI = {
  // Get current settings
  getSettings: async () => {
    const response = await apiClient.get('/api/settings');
    return response.data;
  },

  // Update settings
  updateSettings: async (settings) => {
    const response = await apiClient.put('/api/settings', settings);
    return response.data;
  },

  // Reset to default settings
  resetSettings: async () => {
    const response = await apiClient.post('/api/settings/reset');
    return response.data;
  }
};

/**
 * Statistics API
 */
export const statsAPI = {
  // Get performance statistics
  getPerformanceStats: async (period = '30d') => {
    const response = await apiClient.get('/api/stats/performance', {
      params: { period }
    });
    return response.data;
  },

  // Get signal quality stats
  getSignalQualityStats: async () => {
    const response = await apiClient.get('/api/stats/signal-quality');
    return response.data;
  },

  // Get trade statistics
  getTradeStats: async () => {
    const response = await apiClient.get('/api/stats/trades');
    return response.data;
  }
};

export default apiClient;
