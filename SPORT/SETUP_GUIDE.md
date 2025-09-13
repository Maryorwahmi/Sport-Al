# AI Sports Analyzer Setup Guide

## Quick Start

1. **Clone and Navigate:**
   ```bash
   cd SPORT
   ```

2. **Start with Docker (Recommended):**
   ```bash
   docker-compose up -d
   ```

3. **Or Manual Setup:**

   **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   python app/main.py
   ```

   **Frontend:**
   ```bash
   cd frontend
   npm install
   cp .env.example .env
   npm start
   ```

## System Architecture

```
SPORT/
├── backend/           # FastAPI backend
│   ├── app/          # Main application
│   │   ├── main.py   # FastAPI app
│   │   ├── config.py # Configuration
│   │   ├── sport_db_client.py # SportDB API client
│   │   └── data_service.py    # Data management
│   ├── models/       # ML models
│   │   └── predictor.py # AI prediction engine
│   ├── database/     # Database layer
│   │   ├── database.py # Database connection
│   │   └── models.py   # SQLAlchemy models
│   └── api/          # API routes
│       ├── data_router.py      # Data endpoints
│       ├── prediction_router.py # Prediction endpoints
│       └── training_router.py   # Model training endpoints
├── frontend/         # React frontend
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/     # Page components
│   │   └── services/  # API services
│   └── public/       # Static assets
└── docker/           # Docker configuration
```

## Initial Setup Steps

### 1. Database Setup
```bash
# Using PostgreSQL
createdb sports_db
psql sports_db -c "CREATE USER sports_user WITH PASSWORD 'sports_pass';"
psql sports_db -c "GRANT ALL PRIVILEGES ON DATABASE sports_db TO sports_user;"
```

### 2. Environment Configuration
```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your database credentials

# Frontend
cp frontend/.env.example frontend/.env
# Edit frontend/.env with your API URL
```

### 3. Data Synchronization
```bash
# Generate sample data (for testing)
cd backend
python generate_sample_data.py

# Or sync real data from SportDB API
curl -X GET "http://localhost:8000/api/data/sync"
```

### 4. Train ML Model
```bash
# Train the prediction model
curl -X POST "http://localhost:8000/api/training/train"
```

## API Endpoints

### Data Management
- `GET /api/data/teams` - Get teams
- `GET /api/data/players` - Get players  
- `GET /api/data/matches` - Get matches
- `GET /api/data/search?query=Arsenal` - Search
- `GET /api/data/sync` - Sync data from SportDB

### Predictions
- `POST /api/predictions/predict` - Make prediction
- `GET /api/predictions/upcoming-matches` - Get upcoming matches
- `GET /api/predictions/history` - Get prediction history
- `GET /api/predictions/accuracy` - Get model accuracy

### Training
- `POST /api/training/train` - Train model
- `GET /api/training/status` - Get training status
- `POST /api/training/retrain` - Retrain model

## Frontend Features

### 🏠 Homepage
- System status dashboard
- Statistics overview
- Quick actions

### 🔍 Search Page
- Team, player, and match search
- Filtered browsing
- Detailed team information

### 📊 Evaluation Page
- Team performance analysis
- Historical statistics
- Win rates and metrics

### 🎯 Predictions Page
- AI match predictions
- Upcoming matches
- Prediction accuracy tracking

## Testing

### Backend Testing
```bash
cd backend
python test_structure.py    # Test API structure
python test_sportdb_api.py  # Test SportDB API (requires internet)
```

### Frontend Testing
```bash
cd frontend
npm test
```

## Production Deployment

### Docker Deployment
```bash
# Build and run all services
docker-compose up -d

# Scale services
docker-compose up -d --scale backend=3
```

### Environment Variables
```bash
# Production backend
DATABASE_URL=postgresql://user:pass@db:5432/sports_db
SPORTDB_API_KEY=your_real_api_key

# Production frontend
REACT_APP_API_URL=https://your-api-domain.com
```

## SportDB API Integration

The system uses the SportDB API (https://www.thesportsdb.com) for real sports data:

- **Free tier:** 100 requests/hour
- **Paid tier:** Unlimited requests
- **Data includes:** Teams, players, matches, statistics

### Sample API Calls
```python
# Get Premier League teams
GET https://www.thesportsdb.com/api/v1/json/lookup_all_teams.php?id=4328

# Search for a team
GET https://www.thesportsdb.com/api/v1/json/searchteams.php?t=Arsenal

# Get team players
GET https://www.thesportsdb.com/api/v1/json/lookup_all_players.php?id=133604
```

## Machine Learning Pipeline

### 1. Feature Engineering
- Team form (recent wins/losses)
- Goal statistics
- Home/away performance
- Historical head-to-head

### 2. Model Training
- Algorithm: Random Forest Classifier
- Features: 15+ statistical indicators
- Target: Match outcome (home_win/draw/away_win)

### 3. Prediction Pipeline
- Load historical data
- Extract features for upcoming matches
- Generate probability predictions
- Calculate confidence scores

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql
   
   # Verify credentials in .env file
   ```

2. **SportDB API Timeout**
   ```bash
   # Use sample data instead
   python generate_sample_data.py
   ```

3. **Model Training Error**
   ```bash
   # Ensure sufficient training data (50+ matches)
   curl -X GET "localhost:8000/api/data/matches?limit=100"
   ```

4. **Frontend Build Error**
   ```bash
   # Clear cache and reinstall
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

## Performance Optimization

### Database Optimization
- Index on frequently queried fields
- Connection pooling
- Query optimization

### API Optimization
- Response caching
- Pagination for large datasets
- Background tasks for heavy operations

### Frontend Optimization
- Code splitting
- Lazy loading
- Image optimization

## Monitoring and Logging

### Backend Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### API Monitoring
- Response times
- Error rates
- Database query performance

### Model Performance
- Prediction accuracy tracking
- Model drift detection
- Retraining schedules

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review API documentation
- Open GitHub issue with detailed description