from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.database import Base
from datetime import datetime

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    sport = Column(String)
    league = Column(String)
    country = Column(String)
    founded = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    position = Column(String)
    team_id = Column(Integer, ForeignKey("teams.id"))
    nationality = Column(String)
    birth_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team")

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    match_date = Column(DateTime)
    sport = Column(String)
    league = Column(String)
    season = Column(String)
    round = Column(String)
    
    # Scores
    home_score = Column(Integer)
    away_score = Column(Integer)
    result = Column(String)  # 'home_win', 'away_win', 'draw'
    
    # Status
    status = Column(String)  # 'completed', 'scheduled', 'live'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
    statistics = relationship("MatchStatistics", back_populates="match")

class MatchStatistics(Base):
    __tablename__ = "match_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    
    # Team performance stats
    home_shots = Column(Integer)
    away_shots = Column(Integer)
    home_possession = Column(Float)
    away_possession = Column(Float)
    home_corners = Column(Integer)
    away_corners = Column(Integer)
    home_fouls = Column(Integer)
    away_fouls = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match", back_populates="statistics")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    model_name = Column(String)
    
    # Predictions
    predicted_result = Column(String)  # 'home_win', 'away_win', 'draw'
    home_win_probability = Column(Float)
    away_win_probability = Column(Float)
    draw_probability = Column(Float)
    predicted_score_home = Column(Float)
    predicted_score_away = Column(Float)
    
    # Metadata
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_accurate = Column(Boolean, default=None)  # Set after match completion
    
    # Relationships
    match = relationship("Match")