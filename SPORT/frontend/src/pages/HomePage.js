import React, { useState, useEffect } from 'react';
import { healthCheck, dataAPI, trainingAPI } from '../services/api';

const HomePage = () => {
  const [systemStatus, setSystemStatus] = useState({
    api: 'checking',
    model: 'checking',
    data: 'checking'
  });
  const [stats, setStats] = useState({
    teams: 0,
    players: 0,
    matches: 0
  });

  useEffect(() => {
    checkSystemStatus();
    loadStats();
  }, []);

  const checkSystemStatus = async () => {
    // Check API health
    try {
      await healthCheck();
      setSystemStatus(prev => ({ ...prev, api: 'healthy' }));
    } catch (error) {
      setSystemStatus(prev => ({ ...prev, api: 'error' }));
    }

    // Check model status
    try {
      const response = await trainingAPI.getStatus();
      setSystemStatus(prev => ({ 
        ...prev, 
        model: response.data.model_trained ? 'healthy' : 'needs_training' 
      }));
    } catch (error) {
      setSystemStatus(prev => ({ ...prev, model: 'error' }));
    }

    // Check data availability
    try {
      const response = await dataAPI.getTeams({ limit: 1 });
      setSystemStatus(prev => ({ 
        ...prev, 
        data: response.data.length > 0 ? 'healthy' : 'no_data' 
      }));
    } catch (error) {
      setSystemStatus(prev => ({ ...prev, data: 'error' }));
    }
  };

  const loadStats = async () => {
    try {
      const [teamsRes, playersRes, matchesRes] = await Promise.all([
        dataAPI.getTeams({ limit: 1000 }),
        dataAPI.getPlayers({ limit: 1000 }),
        dataAPI.getMatches({ limit: 1000 })
      ]);

      setStats({
        teams: teamsRes.data.length,
        players: playersRes.data.length,
        matches: matchesRes.data.length
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleDataSync = async () => {
    try {
      await dataAPI.syncData();
      alert('Data sync started in background. Please check back in a few minutes.');
      setTimeout(loadStats, 5000); // Refresh stats after 5 seconds
    } catch (error) {
      alert('Error starting data sync: ' + error.message);
    }
  };

  const handleModelTrain = async () => {
    try {
      await trainingAPI.trainModel();
      alert('Model training started in background. This may take several minutes.');
      setTimeout(checkSystemStatus, 10000); // Check status after 10 seconds
    } catch (error) {
      alert('Error starting model training: ' + error.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'checking': return 'text-yellow-600';
      case 'needs_training': return 'text-orange-600';
      case 'no_data': return 'text-orange-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'healthy': return '✅ Healthy';
      case 'checking': return '⏳ Checking...';
      case 'needs_training': return '⚠️ Needs Training';
      case 'no_data': return '⚠️ No Data';
      case 'error': return '❌ Error';
      default: return '❓ Unknown';
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🏆 AI Sports Analyzer
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Professional AI-powered Sports Analysis and Prediction System
        </p>
        
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <h3 className="font-medium text-gray-700">API Service</h3>
              <p className={`text-lg font-semibold ${getStatusColor(systemStatus.api)}`}>
                {getStatusText(systemStatus.api)}
              </p>
            </div>
            <div className="text-center">
              <h3 className="font-medium text-gray-700">ML Model</h3>
              <p className={`text-lg font-semibold ${getStatusColor(systemStatus.model)}`}>
                {getStatusText(systemStatus.model)}
              </p>
            </div>
            <div className="text-center">
              <h3 className="font-medium text-gray-700">Data</h3>
              <p className={`text-lg font-semibold ${getStatusColor(systemStatus.data)}`}>
                {getStatusText(systemStatus.data)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <div className="text-3xl mb-2">⚽</div>
          <h3 className="text-2xl font-bold text-blue-600">{stats.teams.toLocaleString()}</h3>
          <p className="text-gray-600">Teams</p>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <div className="text-3xl mb-2">👤</div>
          <h3 className="text-2xl font-bold text-green-600">{stats.players.toLocaleString()}</h3>
          <p className="text-gray-600">Players</p>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <div className="text-3xl mb-2">🏟️</div>
          <h3 className="text-2xl font-bold text-purple-600">{stats.matches.toLocaleString()}</h3>
          <p className="text-gray-600">Matches</p>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4 flex items-center">
            <span className="mr-2">🔍</span>
            Search & Discovery
          </h3>
          <p className="text-gray-600 mb-4">
            Search for teams, players, and matches across multiple leagues and competitions.
          </p>
          <a href="/search" className="text-blue-600 hover:text-blue-800 font-medium">
            Start Searching →
          </a>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4 flex items-center">
            <span className="mr-2">📊</span>
            Performance Analysis
          </h3>
          <p className="text-gray-600 mb-4">
            Analyze team performance, statistics, and historical trends.
          </p>
          <a href="/evaluation" className="text-blue-600 hover:text-blue-800 font-medium">
            View Analytics →
          </a>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4 flex items-center">
            <span className="mr-2">🎯</span>
            AI Predictions
          </h3>
          <p className="text-gray-600 mb-4">
            Get AI-powered predictions for upcoming matches with confidence scores.
          </p>
          <a href="/predictions" className="text-blue-600 hover:text-blue-800 font-medium">
            Make Predictions →
          </a>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4 flex items-center">
            <span className="mr-2">🔄</span>
            Data Management
          </h3>
          <p className="text-gray-600 mb-4">
            Sync data from SportDB API and manage machine learning models.
          </p>
          <div className="space-x-2">
            <button
              onClick={handleDataSync}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors text-sm"
            >
              Sync Data
            </button>
            {systemStatus.model === 'needs_training' && (
              <button
                onClick={handleModelTrain}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors text-sm"
              >
                Train Model
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg text-white p-8 text-center">
        <h2 className="text-2xl font-bold mb-4">Ready to Get Started?</h2>
        <p className="text-lg mb-6">
          Explore our comprehensive sports analysis and prediction platform
        </p>
        <div className="space-x-4">
          <a
            href="/search"
            className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-block"
          >
            Search Teams
          </a>
          <a
            href="/predictions"
            className="bg-transparent border-2 border-white text-white px-6 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-colors inline-block"
          >
            View Predictions
          </a>
        </div>
      </div>
    </div>
  );
};

export default HomePage;