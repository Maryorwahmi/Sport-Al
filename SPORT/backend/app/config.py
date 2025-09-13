import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sports_user:sports_pass@localhost/sports_db")
    
    # SportDB API
    SPORTDB_API_KEY = os.getenv("SPORTDB_API_KEY", "123")
    SPORTDB_BASE_URL = "https://www.thesportsdb.com/api/v1/json"
    
    # ML Models
    MODEL_PATH = "models/saved_models"
    RETRAIN_INTERVAL_HOURS = 24
    
    # API Settings
    API_HOST = "0.0.0.0"
    API_PORT = 8000

settings = Settings()