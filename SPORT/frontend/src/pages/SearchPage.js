import React, { useState, useEffect } from 'react';
import { dataAPI } from '../services/api';

const SearchPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState({ teams: [], players: [] });
  const [teams, setTeams] = useState([]);
  const [players, setPlayers] = useState([]);
  const [matches, setMatches] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('search');

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [teamsRes, playersRes, matchesRes] = await Promise.all([
        dataAPI.getTeams({ limit: 20 }),
        dataAPI.getPlayers({ limit: 20 }),
        dataAPI.getMatches({ limit: 20 })
      ]);

      setTeams(teamsRes.data);
      setPlayers(playersRes.data);
      setMatches(matchesRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await dataAPI.search(searchQuery);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTeamSelect = async (team) => {
    setLoading(true);
    try {
      const response = await dataAPI.getTeamDetails(team.id);
      setSelectedTeam(response.data);
    } catch (error) {
      console.error('Error loading team details:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'TBD';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">🔍 Search Sports Data</h1>

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex gap-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search for teams, players, or matches..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="flex space-x-4 border-b border-gray-200">
          {['search', 'teams', 'players', 'matches'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-4 font-medium capitalize ${
                activeTab === tab
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Search Results */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          {searchResults.teams.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Teams</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {searchResults.teams.map((team) => (
                  <div
                    key={team.id}
                    onClick={() => handleTeamSelect(team)}
                    className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <h3 className="font-semibold">{team.name}</h3>
                    <p className="text-gray-600">{team.league}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {searchResults.players.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Players</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {searchResults.players.map((player) => (
                  <div key={player.id} className="p-4 border rounded-lg">
                    <h3 className="font-semibold">{player.name}</h3>
                    <p className="text-gray-600">{player.position}</p>
                    <p className="text-sm text-gray-500">{player.team_name}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {searchQuery && searchResults.teams.length === 0 && searchResults.players.length === 0 && !loading && (
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <p className="text-gray-600">No results found for "{searchQuery}"</p>
            </div>
          )}
        </div>
      )}

      {/* Teams Tab */}
      {activeTab === 'teams' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">All Teams</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams.map((team) => (
              <div
                key={team.id}
                onClick={() => handleTeamSelect(team)}
                className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <h3 className="font-semibold">{team.name}</h3>
                <p className="text-gray-600">{team.league}</p>
                <p className="text-sm text-gray-500">{team.country}</p>
                {team.founded && (
                  <p className="text-sm text-gray-500">Founded: {team.founded}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Players Tab */}
      {activeTab === 'players' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">All Players</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {players.map((player) => (
              <div key={player.id} className="p-4 border rounded-lg">
                <h3 className="font-semibold">{player.name}</h3>
                <p className="text-gray-600">{player.position}</p>
                <p className="text-sm text-gray-500">{player.team_name || 'No team'}</p>
                {player.nationality && (
                  <p className="text-sm text-gray-500">{player.nationality}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Matches Tab */}
      {activeTab === 'matches' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Matches</h2>
          <div className="space-y-4">
            {matches.map((match) => (
              <div key={match.id} className="p-4 border rounded-lg">
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <div className="font-semibold">
                      {match.home_team} vs {match.away_team}
                    </div>
                    <div className="text-sm text-gray-600">
                      {formatDate(match.date)} • {match.league}
                    </div>
                  </div>
                  <div className="text-right">
                    {match.status === 'completed' ? (
                      <div className="text-lg font-bold">
                        {match.home_score} - {match.away_score}
                      </div>
                    ) : (
                      <div className="text-gray-500">
                        {match.status}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Team Details Modal */}
      {selectedTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">{selectedTeam.team.name}</h2>
              <button
                onClick={() => setSelectedTeam(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Team Info</h3>
                <p><strong>League:</strong> {selectedTeam.team.league}</p>
                <p><strong>Country:</strong> {selectedTeam.team.country}</p>
                <p><strong>Sport:</strong> {selectedTeam.team.sport}</p>
                {selectedTeam.team.founded && (
                  <p><strong>Founded:</strong> {selectedTeam.team.founded}</p>
                )}
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">Statistics</h3>
                {selectedTeam.statistics && (
                  <div>
                    <p><strong>Matches:</strong> {selectedTeam.statistics.total_matches}</p>
                    <p><strong>Wins:</strong> {selectedTeam.statistics.wins}</p>
                    <p><strong>Draws:</strong> {selectedTeam.statistics.draws}</p>
                    <p><strong>Losses:</strong> {selectedTeam.statistics.losses}</p>
                    <p><strong>Win Rate:</strong> {selectedTeam.statistics.win_rate}%</p>
                  </div>
                )}
              </div>
            </div>
            
            {selectedTeam.recent_matches && selectedTeam.recent_matches.length > 0 && (
              <div className="mt-6">
                <h3 className="font-semibold mb-2">Recent Matches</h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {selectedTeam.recent_matches.slice(0, 5).map((match) => (
                    <div key={match.id} className="flex justify-between text-sm">
                      <span>vs {match.opponent}</span>
                      <span>{match.score}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {loading && (
        <div className="text-center py-8">
          <div className="text-gray-600">Loading...</div>
        </div>
      )}
    </div>
  );
};

export default SearchPage;