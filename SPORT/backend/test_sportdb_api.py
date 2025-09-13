"""
Test SportDB API endpoints to ensure we can fetch real sports data
"""

import requests
import json

def test_sportdb_endpoints():
    """Test various SportDB API endpoints"""
    base_url = "https://www.thesportsdb.com/api/v1/json"
    
    print("🌐 Testing SportDB API Endpoints...")
    
    # Test 1: Get all leagues
    print("\n📋 Testing: Get all leagues")
    try:
        response = requests.get(f"{base_url}/all_leagues.php", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'leagues' in data and len(data['leagues']) > 0:
            print(f"✅ Found {len(data['leagues'])} leagues")
            # Show first few leagues
            for league in data['leagues'][:5]:
                print(f"   - {league.get('strLeague', 'Unknown')} ({league.get('strSport', 'Unknown')})")
        else:
            print("❌ No leagues found")
    except Exception as e:
        print(f"❌ Error getting leagues: {e}")
    
    # Test 2: Get teams in English Premier League (ID: 4328)
    print("\n⚽ Testing: Get teams in Premier League")
    try:
        response = requests.get(f"{base_url}/lookup_all_teams.php?id=4328", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'teams' in data and data['teams']:
            teams = data['teams']
            print(f"✅ Found {len(teams)} teams in Premier League")
            # Show first few teams
            for team in teams[:5]:
                print(f"   - {team.get('strTeam', 'Unknown')} (Founded: {team.get('intFormedYear', 'Unknown')})")
        else:
            print("❌ No teams found")
    except Exception as e:
        print(f"❌ Error getting teams: {e}")
    
    # Test 3: Search for a specific team (Arsenal)
    print("\n🔍 Testing: Search for Arsenal")
    try:
        response = requests.get(f"{base_url}/searchteams.php?t=Arsenal", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'teams' in data and data['teams']:
            team = data['teams'][0]
            print(f"✅ Found Arsenal: {team.get('strTeam', 'Unknown')}")
            print(f"   - League: {team.get('strLeague', 'Unknown')}")
            print(f"   - Country: {team.get('strCountry', 'Unknown')}")
            print(f"   - Founded: {team.get('intFormedYear', 'Unknown')}")
            
            # Test getting players for this team
            team_id = team.get('idTeam')
            if team_id:
                print(f"\n👥 Testing: Get players for Arsenal (ID: {team_id})")
                try:
                    response = requests.get(f"{base_url}/lookup_all_players.php?id={team_id}", timeout=10)
                    response.raise_for_status()
                    player_data = response.json()
                    
                    if 'player' in player_data and player_data['player']:
                        players = player_data['player']
                        print(f"✅ Found {len(players)} players")
                        # Show first few players
                        for player in players[:3]:
                            print(f"   - {player.get('strPlayer', 'Unknown')} ({player.get('strPosition', 'Unknown')})")
                    else:
                        print("❌ No players found")
                except Exception as e:
                    print(f"❌ Error getting players: {e}")
        else:
            print("❌ Arsenal not found")
    except Exception as e:
        print(f"❌ Error searching for Arsenal: {e}")
    
    # Test 4: Get recent events for Premier League
    print("\n🏟️ Testing: Get recent Premier League events")
    try:
        response = requests.get(f"{base_url}/eventsseason.php?id=4328&s=2023-2024", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'events' in data and data['events']:
            events = data['events'][:5]  # Just first 5
            print(f"✅ Found events for 2023-2024 season")
            for event in events:
                home_team = event.get('strHomeTeam', 'Unknown')
                away_team = event.get('strAwayTeam', 'Unknown')
                date = event.get('dateEvent', 'Unknown')
                home_score = event.get('intHomeScore', 'TBD')
                away_score = event.get('intAwayScore', 'TBD')
                print(f"   - {home_team} vs {away_team} on {date} ({home_score}-{away_score})")
        else:
            print("❌ No events found")
    except Exception as e:
        print(f"❌ Error getting events: {e}")
    
    print("\n🎉 SportDB API Test Complete!")

if __name__ == "__main__":
    test_sportdb_endpoints()