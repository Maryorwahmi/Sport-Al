"""
Simple test script to validate the AI Sports Analyzer API structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock imports for testing
class MockAPI:
    def get(self, path, **kwargs):
        return {"message": f"Mock response for {path}"}
    
    def post(self, path, **kwargs):
        return {"message": f"Mock POST response for {path}"}

class MockSession:
    def get(self, url, **kwargs):
        class MockResponse:
            def json(self):
                return {"message": "Mock SportDB response"}
            def raise_for_status(self):
                pass
        return MockResponse()

# Test the API structure
def test_api_structure():
    print("🔍 Testing AI Sports Analyzer API Structure...")
    
    # Test SportDB Client
    print("\n📡 Testing SportDB Client...")
    try:
        from app.sport_db_client import SportDBClient
        client = SportDBClient()
        print("✅ SportDB Client initialized successfully")
    except Exception as e:
        print(f"❌ SportDB Client error: {e}")
    
    # Test Data Service
    print("\n📊 Testing Data Service...")
    try:
        # We can't test with real DB, but we can check the class structure
        with open('app/data_service.py', 'r') as f:
            content = f.read()
            if 'class DataService' in content:
                print("✅ DataService class found")
            if 'sync_leagues_and_teams' in content:
                print("✅ Data sync methods found")
            if 'get_team_statistics' in content:
                print("✅ Statistics methods found")
    except Exception as e:
        print(f"❌ Data Service error: {e}")
    
    # Test ML Predictor
    print("\n🤖 Testing ML Predictor...")
    try:
        with open('models/predictor.py', 'r') as f:
            content = f.read()
            if 'class SportsPredictor' in content:
                print("✅ SportsPredictor class found")
            if 'train_model' in content:
                print("✅ Training methods found")
            if 'predict_match' in content:
                print("✅ Prediction methods found")
    except Exception as e:
        print(f"❌ ML Predictor error: {e}")
    
    # Test API Routers
    print("\n🌐 Testing API Routers...")
    try:
        with open('api/data_router.py', 'r') as f:
            content = f.read()
            if 'get_teams' in content:
                print("✅ Data router endpoints found")
        
        with open('api/prediction_router.py', 'r') as f:
            content = f.read()
            if 'predict_match' in content:
                print("✅ Prediction router endpoints found")
        
        with open('api/training_router.py', 'r') as f:
            content = f.read()
            if 'train_model' in content:
                print("✅ Training router endpoints found")
    except Exception as e:
        print(f"❌ API Routers error: {e}")
    
    # Test Database Models
    print("\n🗄️ Testing Database Models...")
    try:
        with open('database/models.py', 'r') as f:
            content = f.read()
            models = ['Team', 'Player', 'Match', 'MatchStatistics', 'Prediction']
            for model in models:
                if f'class {model}' in content:
                    print(f"✅ {model} model found")
                else:
                    print(f"❌ {model} model missing")
    except Exception as e:
        print(f"❌ Database Models error: {e}")
    
    print("\n🎉 API Structure Test Complete!")

if __name__ == "__main__":
    test_api_structure()