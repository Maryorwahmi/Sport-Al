// API service for backend communication
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),
  
  // Model training
  trainModel: (data) => api.post('/api/train', data),
  getModelInfo: () => api.get('/api/model/info'),
  
  // Analysis
  analyzeSymbol: (data) => api.post('/api/analyze', data),
  getSignal: (data) => api.post('/api/signal', data),
  scanOpportunities: (data) => api.post('/api/scan', data),
  
  // Backtesting
  runBacktest: (data) => api.post('/api/backtest', data),
  
  // Settings
  getSettings: () => api.get('/api/settings'),
};

export default apiService;
