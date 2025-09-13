import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Data API
export const dataAPI = {
  // Teams
  getTeams: (params = {}) => api.get('/api/data/teams', { params }),
  getTeamDetails: (teamId) => api.get(`/api/data/teams/${teamId}`),
  
  // Players
  getPlayers: (params = {}) => api.get('/api/data/players', { params }),
  
  // Matches
  getMatches: (params = {}) => api.get('/api/data/matches', { params }),
  
  // Search
  search: (query) => api.get('/api/data/search', { params: { query } }),
  
  // Leagues
  getLeagues: () => api.get('/api/data/leagues'),
  
  // Sync data
  syncData: () => api.get('/api/data/sync'),
};

// Prediction API
export const predictionAPI = {
  // Make prediction
  predict: (data) => api.post('/api/predictions/predict', data),
  
  // Get upcoming matches with predictions
  getUpcomingMatches: (params = {}) => api.get('/api/predictions/upcoming-matches', { params }),
  
  // Get prediction history
  getPredictionHistory: (params = {}) => api.get('/api/predictions/history', { params }),
  
  // Get prediction accuracy
  getAccuracy: () => api.get('/api/predictions/accuracy'),
  
  // Batch predict
  batchPredict: () => api.post('/api/predictions/batch-predict'),
};

// Training API
export const trainingAPI = {
  // Train model
  trainModel: () => api.post('/api/training/train'),
  
  // Get training status
  getStatus: () => api.get('/api/training/status'),
  
  // Retrain model
  retrainModel: () => api.post('/api/training/retrain'),
  
  // Get model metrics
  getMetrics: () => api.get('/api/training/metrics'),
  
  // Evaluate model
  evaluateModel: () => api.post('/api/training/evaluate'),
};

// Health check
export const healthCheck = () => api.get('/health');

export default api;