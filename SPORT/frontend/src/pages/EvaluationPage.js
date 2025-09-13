import React, { useState, useEffect } from 'react';
import { dataAPI } from '../services/api';

const EvaluationPage = () => {
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [teamDetails, setTeamDetails] = useState(null);
  const [leagues, setLeagues] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadLeagues();
    loadTeams();
  }, []);

  useEffect(() => {
    if (selectedLeague) {
      loadTeamsByLeague();
    }
  }, [selectedLeague]);

  const loadLeagues = async () => {
    try {
      const response = await dataAPI.getLeagues();
      setLeagues(response.data);
    } catch (error) {
      console.error('Error loading leagues:', error);
    }
  };

  const loadTeams = async () => {
    setLoading(true);
    try {
      const response = await dataAPI.getTeams({ limit: 50 });
      setTeams(response.data);
    } catch (error) {
      console.error('Error loading teams:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTeamsByLeague = async () => {
    setLoading(true);
    try {
      const response = await dataAPI.getTeams({ 
        limit: 100,
        // Note: API doesn't support league filter directly, so we filter client-side
      });
      const filteredTeams = response.data.filter(team => 
        team.league === selectedLeague
      );
      setTeams(filteredTeams);
    } catch (error) {
      console.error('Error loading teams by league:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTeamSelect = async (team) => {
    setSelectedTeam(team);
    setLoading(true);
    try {
      const response = await dataAPI.getTeamDetails(team.id);
      setTeamDetails(response.data);
    } catch (error) {
      console.error('Error loading team details:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPerformanceColor = (winRate) => {
    if (winRate >= 70) return 'text-green-600';
    if (winRate >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getResultBadge = (result) => {
    const badges = {
      home_win: 'bg-green-100 text-green-800',
      away_win: 'bg-green-100 text-green-800',
      draw: 'bg-yellow-100 text-yellow-800',
      loss: 'bg-red-100 text-red-800'
    };
    return badges[result] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'TBD';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">📊 Performance Evaluation</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Team Selection */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
            <h2 className="text-xl font-semibold mb-4">Select Team</h2>
            
            {/* League Filter */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by League
              </label>
              <select
                value={selectedLeague}
                onChange={(e) => setSelectedLeague(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Leagues</option>
                {leagues.map((league) => (
                  <option key={league.name} value={league.name}>
                    {league.name} ({league.team_count})
                  </option>
                ))}
              </select>
            </div>

            {/* Team List */}
            <div className="max-h-96 overflow-y-auto">
              {loading ? (
                <div className="text-center py-4">Loading teams...</div>
              ) : (
                <div className="space-y-2">
                  {teams.map((team) => (
                    <button
                      key={team.id}
                      onClick={() => handleTeamSelect(team)}
                      className={`w-full text-left p-3 rounded-lg border transition-colors ${
                        selectedTeam?.id === team.id
                          ? 'bg-blue-50 border-blue-300'
                          : 'hover:bg-gray-50 border-gray-200'
                      }`}
                    >
                      <div className="font-medium">{team.name}</div>
                      <div className="text-sm text-gray-600">{team.league}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column - Team Details */}
        <div className="lg:col-span-2">
          {!selectedTeam ? (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <div className="text-6xl mb-4">⚽</div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                Select a Team
              </h3>
              <p className="text-gray-600">
                Choose a team from the left panel to view detailed performance analysis
              </p>
            </div>
          ) : loading ? (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <div className="text-gray-600">Loading team details...</div>
            </div>
          ) : teamDetails ? (
            <div className="space-y-6">
              {/* Team Header */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold">{teamDetails.team.name}</h2>
                    <p className="text-gray-600">{teamDetails.team.league}</p>
                    <p className="text-sm text-gray-500">
                      {teamDetails.team.country} • {teamDetails.team.sport}
                    </p>
                  </div>
                  {teamDetails.team.founded && (
                    <div className="text-right">
                      <p className="text-sm text-gray-500">Founded</p>
                      <p className="text-lg font-semibold">{teamDetails.team.founded}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Statistics Cards */}
              {teamDetails.statistics && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white rounded-lg shadow-md p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {teamDetails.statistics.total_matches}
                    </div>
                    <div className="text-sm text-gray-600">Total Matches</div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-4 text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {teamDetails.statistics.wins}
                    </div>
                    <div className="text-sm text-gray-600">Wins</div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-4 text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {teamDetails.statistics.draws}
                    </div>
                    <div className="text-sm text-gray-600">Draws</div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-4 text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {teamDetails.statistics.losses}
                    </div>
                    <div className="text-sm text-gray-600">Losses</div>
                  </div>
                </div>
              )}

              {/* Performance Metrics */}
              {teamDetails.statistics && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-xl font-semibold mb-4">Performance Metrics</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-700">Win Rate</span>
                        <span className={`font-bold ${getPerformanceColor(teamDetails.statistics.win_rate)}`}>
                          {teamDetails.statistics.win_rate}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${teamDetails.statistics.win_rate}%` }}
                        ></div>
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-700">Goals For</span>
                        <span className="font-bold text-green-600">
                          {teamDetails.statistics.goals_for}
                        </span>
                      </div>
                      <div className="text-sm text-gray-500">
                        Avg: {(teamDetails.statistics.goals_for / teamDetails.statistics.total_matches).toFixed(1)} per match
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-700">Goal Difference</span>
                        <span className={`font-bold ${
                          teamDetails.statistics.goal_difference >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {teamDetails.statistics.goal_difference >= 0 ? '+' : ''}{teamDetails.statistics.goal_difference}
                        </span>
                      </div>
                      <div className="text-sm text-gray-500">
                        Goals Against: {teamDetails.statistics.goals_against}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Recent Matches */}
              {teamDetails.recent_matches && teamDetails.recent_matches.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-xl font-semibold mb-4">Recent Matches</h3>
                  <div className="space-y-3">
                    {teamDetails.recent_matches.slice(0, 10).map((match) => (
                      <div key={match.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className={match.is_home ? 'font-medium' : ''}>
                              {match.is_home ? 'vs' : '@'} {match.opponent}
                            </span>
                            {match.result && (
                              <span className={`px-2 py-1 rounded-full text-xs ${getResultBadge(
                                match.is_home 
                                  ? match.result 
                                  : match.result === 'home_win' ? 'away_win' 
                                  : match.result === 'away_win' ? 'home_win' 
                                  : 'draw'
                              )}`}>
                                {match.result === 'draw' ? 'Draw' : 
                                 (match.is_home && match.result === 'home_win') || 
                                 (!match.is_home && match.result === 'away_win') ? 'Win' : 'Loss'}
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-gray-600">
                            {formatDate(match.date)}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium">{match.score}</div>
                          <div className="text-xs text-gray-500 capitalize">{match.status}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <div className="text-red-600 mb-2">⚠️</div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                No Data Available
              </h3>
              <p className="text-gray-600">
                Unable to load details for this team. Please try another team.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EvaluationPage;