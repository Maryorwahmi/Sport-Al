"""
Sample data generator for AI Sports Analyzer
This creates mock data when SportDB API is not available
"""

import json
import random
from datetime import datetime, timedelta

def generate_sample_teams(count=20):
    """Generate sample team data"""
    team_names = [
        "Arsenal", "Chelsea", "Manchester United", "Liverpool", "Manchester City",
        "Tottenham", "Real Madrid", "Barcelona", "Bayern Munich", "PSG",
        "Juventus", "AC Milan", "Inter Milan", "Atletico Madrid", "Borussia Dortmund",
        "Ajax", "Porto", "Benfica", "Celtic", "Rangers"
    ]
    
    leagues = [
        "Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1",
        "Eredivisie", "Primeira Liga", "Scottish Premier League"
    ]
    
    countries = [
        "England", "Spain", "Italy", "Germany", "France",
        "Netherlands", "Portugal", "Scotland"
    ]
    
    teams = []
    for i in range(min(count, len(team_names))):
        teams.append({
            "id": i + 1,
            "name": team_names[i],
            "sport": "Soccer",
            "league": random.choice(leagues),
            "country": random.choice(countries),
            "founded": random.randint(1870, 1990)
        })
    
    return teams

def generate_sample_players(teams, players_per_team=5):
    """Generate sample player data"""
    first_names = [
        "Marcus", "Mohamed", "Kevin", "Virgil", "Harry", "Sadio", "Raheem",
        "Pierre", "Alexandre", "Bruno", "Paul", "N'Golo", "Trent", "Andy",
        "Son", "Gareth", "Christian", "Jadon", "Jack", "Phil"
    ]
    
    last_names = [
        "Rashford", "Salah", "De Bruyne", "van Dijk", "Kane", "Mane", "Sterling",
        "Aubameyang", "Lacazette", "Fernandes", "Pogba", "Kante", "Alexander-Arnold",
        "Robertson", "Heung-min", "Bale", "Pulisic", "Sancho", "Grealish", "Foden"
    ]
    
    positions = ["Forward", "Midfielder", "Defender", "Goalkeeper"]
    
    players = []
    player_id = 1
    
    for team in teams:
        for i in range(players_per_team):
            players.append({
                "id": player_id,
                "name": f"{random.choice(first_names)} {random.choice(last_names)}",
                "position": random.choice(positions),
                "team_id": team["id"],
                "nationality": team["country"],
                "birth_date": datetime.now() - timedelta(days=random.randint(18*365, 35*365))
            })
            player_id += 1
    
    return players

def generate_sample_matches(teams, count=50):
    """Generate sample match data"""
    matches = []
    
    for i in range(count):
        home_team = random.choice(teams)
        away_team = random.choice([t for t in teams if t["id"] != home_team["id"]])
        
        # Generate match date (mix of past and future)
        if random.random() < 0.7:  # 70% completed matches
            match_date = datetime.now() - timedelta(days=random.randint(1, 365))
            status = "completed"
            home_score = random.randint(0, 5)
            away_score = random.randint(0, 5)
            
            if home_score > away_score:
                result = "home_win"
            elif away_score > home_score:
                result = "away_win"
            else:
                result = "draw"
        else:  # 30% upcoming matches
            match_date = datetime.now() + timedelta(days=random.randint(1, 90))
            status = "scheduled"
            home_score = None
            away_score = None
            result = None
        
        matches.append({
            "id": i + 1,
            "home_team_id": home_team["id"],
            "away_team_id": away_team["id"],
            "match_date": match_date.isoformat(),
            "sport": "Soccer",
            "league": home_team["league"],
            "season": "2023-2024",
            "round": f"Round {random.randint(1, 38)}",
            "home_score": home_score,
            "away_score": away_score,
            "result": result,
            "status": status
        })
    
    return matches

def save_sample_data():
    """Generate and save sample data to JSON files"""
    print("Generating sample data...")
    
    teams = generate_sample_teams(20)
    players = generate_sample_players(teams, 5)
    matches = generate_sample_matches(teams, 100)
    
    # Save to JSON files
    with open('sample_teams.json', 'w') as f:
        json.dump(teams, f, indent=2)
    
    with open('sample_players.json', 'w') as f:
        json.dump(players, f, indent=2, default=str)
    
    with open('sample_matches.json', 'w') as f:
        json.dump(matches, f, indent=2, default=str)
    
    print(f"✅ Generated {len(teams)} teams, {len(players)} players, {len(matches)} matches")
    print("📁 Saved to: sample_teams.json, sample_players.json, sample_matches.json")

if __name__ == "__main__":
    save_sample_data()