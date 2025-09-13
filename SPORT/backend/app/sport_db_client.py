import requests
import logging
from typing import List, Dict, Optional
from app.config import settings

class SportDBClient:
    def __init__(self):
        self.base_url = settings.SPORTDB_BASE_URL
        self.api_key = settings.SPORTDB_API_KEY
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request to SportDB"""
        try:
            url = f"{self.base_url}/{endpoint}"
            if params is None:
                params = {}
            
            # Add API key if required
            if self.api_key != "123":  # Use real API key if available
                params['key'] = self.api_key
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return None

    def get_all_leagues(self) -> List[Dict]:
        """Get all available leagues"""
        data = self._make_request("all_leagues.php")
        if data and 'leagues' in data:
            return data['leagues']
        return []

    def get_teams_in_league(self, league_id: str) -> List[Dict]:
        """Get all teams in a specific league"""
        data = self._make_request("lookup_all_teams.php", {"id": league_id})
        if data and 'teams' in data:
            return data['teams']
        return []

    def get_team_details(self, team_id: str) -> Optional[Dict]:
        """Get detailed information about a team"""
        data = self._make_request("lookupteam.php", {"id": team_id})
        if data and 'teams' in data and data['teams']:
            return data['teams'][0]
        return None

    def get_players_in_team(self, team_id: str) -> List[Dict]:
        """Get all players in a team"""
        data = self._make_request("lookup_all_players.php", {"id": team_id})
        if data and 'player' in data:
            return data['player']
        return []

    def search_teams(self, team_name: str) -> List[Dict]:
        """Search for teams by name"""
        data = self._make_request("searchteams.php", {"t": team_name})
        if data and 'teams' in data:
            return data['teams']
        return []

    def search_players(self, player_name: str) -> List[Dict]:
        """Search for players by name"""
        data = self._make_request("searchplayers.php", {"p": player_name})
        if data and 'player' in data:
            return data['player']
        return []

    def get_next_matches(self, team_id: str, count: int = 5) -> List[Dict]:
        """Get next matches for a team"""
        data = self._make_request("eventsnext.php", {"id": team_id})
        if data and 'events' in data:
            return data['events'][:count]
        return []

    def get_last_matches(self, team_id: str, count: int = 5) -> List[Dict]:
        """Get last matches for a team"""
        data = self._make_request("eventslast.php", {"id": team_id})
        if data and 'results' in data:
            return data['results'][:count]
        return []

    def get_league_events(self, league_id: str, season: str = "2023-2024") -> List[Dict]:
        """Get all events in a league for a season"""
        data = self._make_request("eventsseason.php", {"id": league_id, "s": season})
        if data and 'events' in data:
            return data['events']
        return []

    def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Get detailed information about a match"""
        data = self._make_request("lookupevent.php", {"id": match_id})
        if data and 'events' in data and data['events']:
            return data['events'][0]
        return None

# Create a global instance
sport_db_client = SportDBClient()