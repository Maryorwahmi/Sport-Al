# AI Sports Analyzer (Full-Stack Project)

A professional AI-powered Sports Analyzer system with three major components:

## 1. Data Generator (Backend Data Fetcher)
- Uses **SportDB API** to fetch historical sports data
- Stores data in PostgreSQL database
- Implements periodic data updates
- Provides cleaned, normalized data for analysis

## 2. Trainer (AI/ML Model)
- Training pipeline for historical sports data
- Match outcome prediction models
- Evaluation metrics and performance tracking
- Model retraining capabilities

## 3. Dynamic Frontend (React)
- Homepage with system overview
- Search functionality for teams, players, matches
- Evaluation page for historical performance
- Prediction page with AI-generated forecasts

## Architecture

```
SPORT/
├── backend/           # FastAPI backend services
│   ├── app/          # Main application
│   ├── models/       # ML models and training
│   ├── database/     # Database schemas and operations
│   └── api/          # API endpoints
├── frontend/         # React frontend
│   ├── src/          # Source code
│   └── public/       # Static assets
└── docker/           # Docker configuration
```

## Quick Start

1. **Backend Setup:**
   ```bash
   cd SPORT/backend
   pip install -r requirements.txt
   python app/main.py
   ```

2. **Frontend Setup:**
   ```bash
   cd SPORT/frontend
   npm install
   npm start
   ```

3. **Docker Setup:**
   ```bash
   docker-compose up
   ```

## Features

- ✅ SportDB API integration
- ✅ PostgreSQL database
- ✅ ML prediction models
- ✅ React frontend
- ✅ Docker containerization
- ✅ RESTful API endpoints
- ✅ Real-time predictions