import React, { useState, useEffect } from 'react';
import { predictionAPI, dataAPI, trainingAPI } from '../services/api';

const PredictionPage = () => {
  const [teams, setTeams] = useState([]);
  const [selectedHomeTeam, setSelectedHomeTeam] = useState('');
  const [selectedAwayTeam, setSelectedAwayTeam] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [predictionHistory, setPredictionHistory] = useState([]);
  const [upcomingMatches, setUpcomingMatches] = useState([]);
  const [accuracy, setAccuracy] = useState(null);
  const [modelStatus, setModelStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('predict');

  useEffect(() => {
    loadTeams();
    loadPredictionHistory();
    loadUpcomingMatches();
    loadAccuracy();
    checkModelStatus();
  }, []);

  const loadTeams = async () => {
    try {
      const response = await dataAPI.getTeams({ limit: 200 });
      setTeams(response.data);
    } catch (error) {
      console.error('Error loading teams:', error);
    }
  };

  const loadPredictionHistory = async () => {
    try {
      const response = await predictionAPI.getPredictionHistory({ limit: 20 });
      setPredictionHistory(response.data);
    } catch (error) {
      console.error('Error loading prediction history:', error);
    }
  };

  const loadUpcomingMatches = async () => {
    try {
      const response = await predictionAPI.getUpcomingMatches({ limit: 15 });
      setUpcomingMatches(response.data);
    } catch (error) {
      console.error('Error loading upcoming matches:', error);
    }
  };

  const loadAccuracy = async () => {
    try {
      const response = await predictionAPI.getAccuracy();
      setAccuracy(response.data);
    } catch (error) {
      console.error('Error loading accuracy:', error);
    }
  };

  const checkModelStatus = async () => {
    try {
      const response = await trainingAPI.getStatus();
      setModelStatus(response.data);
    } catch (error) {
      console.error('Error checking model status:', error);
    }
  };

  const handlePredict = async () => {
    if (!selectedHomeTeam || !selectedAwayTeam) {
      alert('Please select both home and away teams');
      return;
    }

    if (selectedHomeTeam === selectedAwayTeam) {
      alert('Home and away teams must be different');
      return;
    }

    setLoading(true);
    try {
      const response = await predictionAPI.predict({
        home_team_id: parseInt(selectedHomeTeam),
        away_team_id: parseInt(selectedAwayTeam)
      });
      setPrediction(response.data);
      
      // Refresh prediction history
      loadPredictionHistory();
    } catch (error) {
      console.error('Error making prediction:', error);
      alert('Error making prediction: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleBatchPredict = async () => {
    setLoading(true);
    try {
      const response = await predictionAPI.batchPredict();
      alert(response.data.message);
      loadUpcomingMatches();
    } catch (error) {
      console.error('Error with batch prediction:', error);
      alert('Error with batch prediction: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  };

  const getProbabilityBarColor = (type) => {
    switch (type) {
      case 'home_win': return 'bg-blue-500';
      case 'draw': return 'bg-yellow-500';
      case 'away_win': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'TBD';
    return new Date(dateString).toLocaleDateString();
  };

  const getTeamName = (teamId) => {
    const team = teams.find(t => t.id === parseInt(teamId));
    return team ? team.name : 'Select Team';
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">🎯 AI Predictions</h1>

      {/* Model Status Warning */}
      {modelStatus && !modelStatus.model_trained && (
        <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 mb-6">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                <strong>Warning:</strong> The prediction model is not trained yet. Please train the model first to get accurate predictions.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6">
        <div className="flex space-x-4 border-b border-gray-200">
          {['predict', 'upcoming', 'history', 'accuracy'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-4 font-medium capitalize ${
                activeTab === tab
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'predict' ? 'Make Prediction' : tab}
            </button>
          ))}
        </div>
      </div>

      {/* Make Prediction Tab */}
      {activeTab === 'predict' && (
        <div className="space-y-6">
          {/* Prediction Form */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Predict Match Outcome</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Home Team
                </label>
                <select
                  value={selectedHomeTeam}
                  onChange={(e) => setSelectedHomeTeam(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select Home Team</option>
                  {teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name} ({team.league})
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Away Team
                </label>
                <select
                  value={selectedAwayTeam}
                  onChange={(e) => setSelectedAwayTeam(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select Away Team</option>
                  {teams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name} ({team.league})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            <button
              onClick={handlePredict}
              disabled={loading || !selectedHomeTeam || !selectedAwayTeam || !modelStatus?.model_trained}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Predicting...' : 'Predict Outcome'}
            </button>
          </div>

          {/* Prediction Result */}
          {prediction && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Prediction Result</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold mb-2">Match</h3>
                  <p className="text-lg">
                    <strong>{prediction.prediction.home_team}</strong> vs <strong>{prediction.prediction.away_team}</strong>
                  </p>
                  <p className="text-sm text-gray-600">{formatDate(prediction.prediction.match_date)}</p>
                </div>
                
                <div>
                  <h3 className="font-semibold mb-2">Prediction</h3>
                  <p className="text-lg font-bold text-blue-600">
                    {prediction.prediction.predicted_result.replace('_', ' ').toUpperCase()}
                  </p>
                  <p className={`text-sm ${getConfidenceColor(prediction.confidence)}`}>
                    Confidence: {getConfidenceLabel(prediction.confidence)} ({(prediction.confidence * 100).toFixed(1)}%)
                  </p>
                </div>
              </div>
              
              <div className="mt-6">
                <h3 className="font-semibold mb-4">Probability Breakdown</h3>
                <div className="space-y-3">
                  {Object.entries(prediction.probabilities).map(([outcome, probability]) => (
                    <div key={outcome}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="capitalize">{outcome.replace('_', ' ')}</span>
                        <span className="font-medium">{(probability * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getProbabilityBarColor(outcome)}`}
                          style={{ width: `${probability * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Upcoming Matches Tab */}
      {activeTab === 'upcoming' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Upcoming Matches</h2>
            <button
              onClick={handleBatchPredict}
              disabled={loading || !modelStatus?.model_trained}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Generate All Predictions'}
            </button>
          </div>
          
          <div className="space-y-4">
            {upcomingMatches.map((match) => (
              <div key={match.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-semibold text-lg">
                      {match.home_team?.name} vs {match.away_team?.name}
                    </div>
                    <div className="text-sm text-gray-600">
                      {formatDate(match.date)} • {match.league}
                    </div>
                  </div>
                  
                  {match.prediction ? (
                    <div className="text-right ml-4">
                      <div className="font-semibold text-blue-600">
                        {match.prediction.predicted_result.replace('_', ' ').toUpperCase()}
                      </div>
                      <div className={`text-sm ${getConfidenceColor(match.prediction.confidence)}`}>
                        {getConfidenceLabel(match.prediction.confidence)} Confidence
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Win: {(match.prediction.probabilities.home_win * 100).toFixed(0)}% | 
                        Draw: {(match.prediction.probabilities.draw * 100).toFixed(0)}% | 
                        Loss: {(match.prediction.probabilities.away_win * 100).toFixed(0)}%
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500 ml-4">
                      No prediction
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {upcomingMatches.length === 0 && (
              <div className="text-center py-8 text-gray-600">
                No upcoming matches found
              </div>
            )}
          </div>
        </div>
      )}

      {/* Prediction History Tab */}
      {activeTab === 'history' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Prediction History</h2>
          
          <div className="space-y-4">
            {predictionHistory.map((pred) => (
              <div key={pred.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-semibold">
                      {pred.home_team} vs {pred.away_team}
                    </div>
                    <div className="text-sm text-gray-600">
                      {formatDate(pred.created_at)}
                    </div>
                  </div>
                  
                  <div className="text-right ml-4">
                    <div className="font-semibold text-blue-600">
                      Predicted: {pred.predicted_result.replace('_', ' ').toUpperCase()}
                    </div>
                    {pred.actual_result && (
                      <div className="text-sm">
                        <span className="text-gray-600">Actual: </span>
                        <span className="font-medium">
                          {pred.actual_result.replace('_', ' ').toUpperCase()}
                        </span>
                        {pred.actual_score && (
                          <span className="text-gray-600"> ({pred.actual_score})</span>
                        )}
                      </div>
                    )}
                    {pred.is_accurate !== null && (
                      <div className={`text-sm font-medium ${
                        pred.is_accurate ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {pred.is_accurate ? '✓ Correct' : '✗ Incorrect'}
                      </div>
                    )}
                    <div className={`text-sm ${getConfidenceColor(pred.confidence)}`}>
                      {getConfidenceLabel(pred.confidence)} Confidence
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {predictionHistory.length === 0 && (
              <div className="text-center py-8 text-gray-600">
                No prediction history found
              </div>
            )}
          </div>
        </div>
      )}

      {/* Accuracy Tab */}
      {activeTab === 'accuracy' && (
        <div className="space-y-6">
          {accuracy ? (
            <>
              {/* Overall Accuracy */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4">Model Performance</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {accuracy.overall_accuracy}%
                    </div>
                    <div className="text-gray-600">Overall Accuracy</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {accuracy.accurate_predictions}
                    </div>
                    <div className="text-gray-600">Correct Predictions</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-3xl font-bold text-gray-600">
                      {accuracy.total_predictions}
                    </div>
                    <div className="text-gray-600">Total Predictions</div>
                  </div>
                </div>
              </div>

              {/* Accuracy by Result Type */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4">Accuracy by Prediction Type</h2>
                
                <div className="space-y-4">
                  {Object.entries(accuracy.by_result_type).map(([type, data]) => (
                    <div key={type} className="border rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium capitalize">{type.replace('_', ' ')}</span>
                        <span className="font-bold text-blue-600">{data.accuracy}%</span>
                      </div>
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>Correct: {data.accurate}</span>
                        <span>Total: {data.total}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${data.accuracy}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="text-gray-600">Loading accuracy data...</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PredictionPage;