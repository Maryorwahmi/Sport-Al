from sqlalchemy.orm import Session
from database.models import Team, Player, Match, MatchStatistics
from app.sport_db_client import sport_db_client
from datetime import datetime
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self, db: Session):
        self.db = db

    def sync_leagues_and_teams(self) -> Dict[str, int]:
        """Sync all leagues and teams from SportDB API"""
        stats = {"leagues": 0, "teams": 0, "players": 0}
        
        try:
            # Get all leagues
            leagues = sport_db_client.get_all_leagues()
            logger.info(f"Found {len(leagues)} leagues")
            
            for league in leagues:
                if not league or 'idLeague' not in league:
                    continue
                    
                league_id = league['idLeague']
                league_name = league.get('strLeague', 'Unknown')
                
                # Get teams in this league
                teams = sport_db_client.get_teams_in_league(league_id)
                logger.info(f"Found {len(teams)} teams in {league_name}")
                
                for team_data in teams:
                    if not team_data or 'idTeam' not in team_data:
                        continue
                        
                    team = self._create_or_update_team(team_data, league_name)
                    if team:
                        stats["teams"] += 1
                        
                        # Get players for this team
                        players = sport_db_client.get_players_in_team(team_data['idTeam'])
                        for player_data in players:
                            if self._create_or_update_player(player_data, team.id):
                                stats["players"] += 1
                
                stats["leagues"] += 1
                
        except Exception as e:
            logger.error(f"Error syncing data: {e}")
            
        return stats

    def _create_or_update_team(self, team_data: Dict, league: str) -> Optional[Team]:
        """Create or update a team record"""
        try:
            team_id = int(team_data['idTeam'])
            existing_team = self.db.query(Team).filter(Team.id == team_id).first()
            
            if existing_team:
                # Update existing team
                existing_team.name = team_data.get('strTeam', existing_team.name)
                existing_team.league = league
                existing_team.country = team_data.get('strCountry', existing_team.country)
                existing_team.founded = self._parse_year(team_data.get('intFormedYear'))
            else:
                # Create new team
                existing_team = Team(
                    id=team_id,
                    name=team_data.get('strTeam', 'Unknown'),
                    sport=team_data.get('strSport', 'Soccer'),
                    league=league,
                    country=team_data.get('strCountry', 'Unknown'),
                    founded=self._parse_year(team_data.get('intFormedYear'))
                )
                self.db.add(existing_team)
            
            self.db.commit()
            return existing_team
            
        except Exception as e:
            logger.error(f"Error creating/updating team: {e}")
            self.db.rollback()
            return None

    def _create_or_update_player(self, player_data: Dict, team_id: int) -> bool:
        """Create or update a player record"""
        try:
            if not player_data or 'idPlayer' not in player_data:
                return False
                
            player_id = int(player_data['idPlayer'])
            existing_player = self.db.query(Player).filter(Player.id == player_id).first()
            
            if existing_player:
                # Update existing player
                existing_player.name = player_data.get('strPlayer', existing_player.name)
                existing_player.position = player_data.get('strPosition', existing_player.position)
                existing_player.nationality = player_data.get('strNationality', existing_player.nationality)
                existing_player.team_id = team_id
            else:
                # Create new player
                existing_player = Player(
                    id=player_id,
                    name=player_data.get('strPlayer', 'Unknown'),
                    position=player_data.get('strPosition', 'Unknown'),
                    team_id=team_id,
                    nationality=player_data.get('strNationality', 'Unknown'),
                    birth_date=self._parse_date(player_data.get('dateBorn'))
                )
                self.db.add(existing_player)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error creating/updating player: {e}")
            self.db.rollback()
            return False

    def sync_matches_for_league(self, league_id: str, season: str = "2023-2024") -> int:
        """Sync matches for a specific league and season"""
        matches_synced = 0
        
        try:
            events = sport_db_client.get_league_events(league_id, season)
            logger.info(f"Found {len(events)} events for league {league_id}")
            
            for event_data in events:
                if self._create_or_update_match(event_data):
                    matches_synced += 1
                    
        except Exception as e:
            logger.error(f"Error syncing matches: {e}")
            
        return matches_synced

    def _create_or_update_match(self, event_data: Dict) -> bool:
        """Create or update a match record"""
        try:
            if not event_data or 'idEvent' not in event_data:
                return False
                
            match_id = int(event_data['idEvent'])
            existing_match = self.db.query(Match).filter(Match.id == match_id).first()
            
            home_team_id = int(event_data.get('idHomeTeam', 0)) if event_data.get('idHomeTeam') else None
            away_team_id = int(event_data.get('idAwayTeam', 0)) if event_data.get('idAwayTeam') else None
            
            if not home_team_id or not away_team_id:
                return False
            
            if existing_match:
                # Update existing match
                existing_match.match_date = self._parse_datetime(event_data.get('dateEvent'), event_data.get('strTime'))
                existing_match.home_score = self._parse_int(event_data.get('intHomeScore'))
                existing_match.away_score = self._parse_int(event_data.get('intAwayScore'))
                existing_match.result = self._determine_result(existing_match.home_score, existing_match.away_score)
                existing_match.status = 'completed' if existing_match.home_score is not None else 'scheduled'
            else:
                # Create new match
                existing_match = Match(
                    id=match_id,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    match_date=self._parse_datetime(event_data.get('dateEvent'), event_data.get('strTime')),
                    sport=event_data.get('strSport', 'Soccer'),
                    league=event_data.get('strLeague', 'Unknown'),
                    season=event_data.get('strSeason', '2023-2024'),
                    round=event_data.get('intRound'),
                    home_score=self._parse_int(event_data.get('intHomeScore')),
                    away_score=self._parse_int(event_data.get('intAwayScore')),
                    status='completed' if event_data.get('intHomeScore') is not None else 'scheduled'
                )
                existing_match.result = self._determine_result(existing_match.home_score, existing_match.away_score)
                self.db.add(existing_match)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error creating/updating match: {e}")
            self.db.rollback()
            return False

    def _parse_int(self, value) -> Optional[int]:
        """Safely parse integer"""
        try:
            return int(value) if value else None
        except (ValueError, TypeError):
            return None

    def _parse_year(self, value) -> Optional[int]:
        """Safely parse year"""
        return self._parse_int(value)

    def _parse_date(self, date_str) -> Optional[datetime]:
        """Safely parse date string"""
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            pass
        return None

    def _parse_datetime(self, date_str, time_str) -> Optional[datetime]:
        """Parse date and time strings"""
        try:
            if date_str:
                date_part = datetime.strptime(date_str, '%Y-%m-%d')
                if time_str:
                    time_part = datetime.strptime(time_str, '%H:%M:%S').time()
                    return datetime.combine(date_part.date(), time_part)
                return date_part
        except (ValueError, TypeError):
            pass
        return None

    def _determine_result(self, home_score: Optional[int], away_score: Optional[int]) -> Optional[str]:
        """Determine match result"""
        if home_score is None or away_score is None:
            return None
            
        if home_score > away_score:
            return 'home_win'
        elif away_score > home_score:
            return 'away_win'
        else:
            return 'draw'

    def get_team_statistics(self, team_id: int) -> Dict:
        """Get comprehensive team statistics"""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return {}
            
        # Get home and away matches
        home_matches = self.db.query(Match).filter(
            Match.home_team_id == team_id,
            Match.status == 'completed'
        ).all()
        
        away_matches = self.db.query(Match).filter(
            Match.away_team_id == team_id,
            Match.status == 'completed'
        ).all()
        
        total_matches = len(home_matches) + len(away_matches)
        wins = 0
        draws = 0
        losses = 0
        goals_for = 0
        goals_against = 0
        
        # Calculate home statistics
        for match in home_matches:
            goals_for += match.home_score or 0
            goals_against += match.away_score or 0
            
            if match.result == 'home_win':
                wins += 1
            elif match.result == 'draw':
                draws += 1
            else:
                losses += 1
        
        # Calculate away statistics
        for match in away_matches:
            goals_for += match.away_score or 0
            goals_against += match.home_score or 0
            
            if match.result == 'away_win':
                wins += 1
            elif match.result == 'draw':
                draws += 1
            else:
                losses += 1
        
        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
        
        return {
            "team_name": team.name,
            "total_matches": total_matches,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goals_for - goals_against,
            "win_rate": round(win_rate, 2),
            "points": wins * 3 + draws  # Assuming 3 points for win, 1 for draw
        }