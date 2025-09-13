from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Team, Player, Match
from app.data_service import DataService
from app.sport_db_client import sport_db_client
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/sync", response_model=Dict)
async def sync_all_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger a full data sync from SportDB API"""
    def sync_data():
        try:
            data_service = DataService(db)
            stats = data_service.sync_leagues_and_teams()
            logger.info(f"Data sync completed: {stats}")
        except Exception as e:
            logger.error(f"Data sync failed: {e}")
    
    background_tasks.add_task(sync_data)
    return {"message": "Data sync started in background"}

@router.get("/teams", response_model=List[Dict])
async def get_teams(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get teams with optional search"""
    query = db.query(Team)
    
    if search:
        query = query.filter(Team.name.ilike(f"%{search}%"))
    
    teams = query.offset(offset).limit(limit).all()
    
    return [
        {
            "id": team.id,
            "name": team.name,
            "sport": team.sport,
            "league": team.league,
            "country": team.country,
            "founded": team.founded
        }
        for team in teams
    ]

@router.get("/teams/{team_id}", response_model=Dict)
async def get_team_details(team_id: int, db: Session = Depends(get_db)):
    """Get detailed team information"""
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team statistics
    data_service = DataService(db)
    stats = data_service.get_team_statistics(team_id)
    
    # Get recent matches
    recent_matches = db.query(Match).filter(
        (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
    ).order_by(Match.match_date.desc()).limit(10).all()
    
    matches_data = []
    for match in recent_matches:
        is_home = match.home_team_id == team_id
        opponent_id = match.away_team_id if is_home else match.home_team_id
        opponent = db.query(Team).filter(Team.id == opponent_id).first()
        
        matches_data.append({
            "id": match.id,
            "date": match.match_date.isoformat() if match.match_date else None,
            "opponent": opponent.name if opponent else "Unknown",
            "is_home": is_home,
            "score": f"{match.home_score}-{match.away_score}" if match.home_score is not None else "TBD",
            "result": match.result,
            "status": match.status
        })
    
    return {
        "team": {
            "id": team.id,
            "name": team.name,
            "sport": team.sport,
            "league": team.league,
            "country": team.country,
            "founded": team.founded
        },
        "statistics": stats,
        "recent_matches": matches_data
    }

@router.get("/players", response_model=List[Dict])
async def get_players(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    team_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get players with optional filters"""
    query = db.query(Player)
    
    if search:
        query = query.filter(Player.name.ilike(f"%{search}%"))
    
    if team_id:
        query = query.filter(Player.team_id == team_id)
    
    players = query.offset(offset).limit(limit).all()
    
    return [
        {
            "id": player.id,
            "name": player.name,
            "position": player.position,
            "nationality": player.nationality,
            "team_name": player.team.name if player.team else None
        }
        for player in players
    ]

@router.get("/matches", response_model=List[Dict])
async def get_matches(
    limit: int = 50,
    offset: int = 0,
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get matches with optional filters"""
    query = db.query(Match)
    
    if team_id:
        query = query.filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        )
    
    if status:
        query = query.filter(Match.status == status)
    
    matches = query.order_by(Match.match_date.desc()).offset(offset).limit(limit).all()
    
    results = []
    for match in matches:
        home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
        
        results.append({
            "id": match.id,
            "date": match.match_date.isoformat() if match.match_date else None,
            "home_team": home_team.name if home_team else "Unknown",
            "away_team": away_team.name if away_team else "Unknown",
            "home_score": match.home_score,
            "away_score": match.away_score,
            "result": match.result,
            "status": match.status,
            "league": match.league
        })
    
    return results

@router.get("/search", response_model=Dict)
async def search_all(query: str, db: Session = Depends(get_db)):
    """Search across teams, players, and matches"""
    # Search teams
    teams = db.query(Team).filter(Team.name.ilike(f"%{query}%")).limit(10).all()
    
    # Search players
    players = db.query(Player).filter(Player.name.ilike(f"%{query}%")).limit(10).all()
    
    return {
        "teams": [
            {
                "id": team.id,
                "name": team.name,
                "league": team.league,
                "type": "team"
            }
            for team in teams
        ],
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "team_name": player.team.name if player.team else None,
                "type": "player"
            }
            for player in players
        ]
    }

@router.get("/leagues", response_model=List[Dict])
async def get_leagues(db: Session = Depends(get_db)):
    """Get all leagues"""
    # Get unique leagues from teams
    leagues = db.query(Team.league).distinct().all()
    
    result = []
    for league_tuple in leagues:
        league = league_tuple[0]
        if league and league != "Unknown":
            team_count = db.query(Team).filter(Team.league == league).count()
            result.append({
                "name": league,
                "team_count": team_count
            })
    
    return sorted(result, key=lambda x: x["team_count"], reverse=True)

@router.post("/teams/{team_id}/sync-matches")
async def sync_team_matches(team_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sync matches for a specific team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    def sync_matches():
        try:
            # Get next and last matches for the team
            next_matches = sport_db_client.get_next_matches(str(team_id))
            last_matches = sport_db_client.get_last_matches(str(team_id))
            
            logger.info(f"Syncing {len(next_matches + last_matches)} matches for team {team.name}")
        except Exception as e:
            logger.error(f"Failed to sync matches for team {team_id}: {e}")
    
    background_tasks.add_task(sync_matches)
    return {"message": f"Match sync started for {team.name}"}