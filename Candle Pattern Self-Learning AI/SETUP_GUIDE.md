# Setup Guide - Candle Pattern Self-Learning AI

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Development Setup](#development-setup)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Software Requirements
- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **npm or yarn** (package manager)
- **Git** (version control)
- **Docker** (optional, for containerized deployment)

### Optional
- **MetaTrader 5** (for live market data)
- **PostgreSQL** (for persistent storage)

---

## Quick Start

### Option 1: Automated Start (Recommended)

**Linux/Mac:**
```bash
cd "Candle Pattern Self-Learning AI"
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
cd "Candle Pattern Self-Learning AI"
start.bat
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Option 2: Manual Start

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python api/server.py
```

**Frontend (new terminal):**
```bash
cd frontend
npm install
npm start
```

---

## Development Setup

### Backend Setup

1. **Create Virtual Environment (Recommended)**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Optional: Install MT5 Support**
```bash
pip install MetaTrader5
```

4. **Optional: Install Deep Learning**
```bash
pip install tensorflow  # For LSTM/CNN models
# OR
pip install torch       # For PyTorch models
```

5. **Run Backend**
```bash
python api/server.py
```

### Frontend Setup

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Configure Environment**
Create `.env` file:
```env
REACT_APP_API_URL=http://localhost:8000
```

3. **Run Development Server**
```bash
npm start
```

4. **Build for Production**
```bash
npm run build
```

---

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Build and Start Services**
```bash
docker-compose up -d
```

2. **View Logs**
```bash
docker-compose logs -f
```

3. **Stop Services**
```bash
docker-compose down
```

### Manual Docker Build

**Backend:**
```bash
docker build -f Dockerfile.backend -t candle-ai-backend .
docker run -p 8000:8000 candle-ai-backend
```

**Frontend:**
```bash
docker build -f Dockerfile.frontend -t candle-ai-frontend .
docker run -p 3000:80 candle-ai-frontend
```

---

## Production Deployment

### Backend (FastAPI)

**Using Uvicorn:**
```bash
cd backend
uvicorn api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

**Using Gunicorn:**
```bash
pip install gunicorn
gunicorn api.server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (React)

1. **Build Production Bundle**
```bash
cd frontend
npm run build
```

2. **Serve with Nginx**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/build;
        try_files $uri /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

3. **Or Use Node Server**
```bash
npm install -g serve
serve -s build -l 3000
```

---

## Configuration

### Backend Settings

Edit `backend/config/settings.py`:

```python
# Data Settings
symbols = ["EURUSD", "GBPUSD", "USDJPY"]
timeframes = [Timeframe.H4, Timeframe.H1, Timeframe.M15]

# ML Settings
window_size = 20
n_clusters = 50
min_pattern_confidence = 0.6

# Risk Settings
risk_per_trade = 0.01        # 1% per trade
max_concurrent_trades = 3
min_rr_ratio = 2.0

# Backtest Settings
initial_balance = 10000.0
commission_pips = 0.8
```

### Frontend Settings

Edit `frontend/.env`:

```env
# API URL
REACT_APP_API_URL=http://localhost:8000

# Optional: Custom port
PORT=3000
```

---

## Testing

### Backend Tests

```bash
cd "Candle Pattern Self-Learning AI"
python test_system.py
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Integration Tests

```bash
# Start backend
cd backend
python api/server.py &

# Run demo
cd ..
python demo.py
```

---

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process or change port in configuration
```

**2. Module Import Errors**
```bash
# Ensure you're in the correct directory
cd "Candle Pattern Self-Learning AI"

# Reinstall dependencies
pip install -r backend/requirements.txt
npm install --prefix frontend
```

**3. CORS Errors**
- Check that backend allows frontend origin
- Verify REACT_APP_API_URL in frontend/.env

**4. Model Not Trained**
- Navigate to Training page
- Click "Start Training" button
- Wait for completion (2-5 minutes)

**5. Data Fetching Issues**
- System uses mock data by default
- For live data, install MetaTrader 5:
  ```bash
  pip install MetaTrader5
  ```

### Performance Optimization

**Backend:**
- Increase worker processes for production
- Use caching for frequently accessed data
- Optimize database queries

**Frontend:**
- Enable production build optimizations
- Use code splitting for large components
- Implement lazy loading

### Logs and Debugging

**Backend Logs:**
```bash
# Check backend logs
tail -f backend/api/server.log
```

**Frontend Logs:**
- Open browser Developer Tools (F12)
- Check Console tab for errors
- Check Network tab for API calls

---

## Next Steps

1. **Train the Model**
   - Go to Training page
   - Configure symbol and timeframe
   - Start training

2. **Run Backtests**
   - Go to Backtest page
   - Configure parameters
   - Analyze results

3. **Monitor Signals**
   - Go to Dashboard
   - Scan markets for opportunities
   - Review trading signals

4. **Customize Settings**
   - Adjust risk parameters
   - Configure confluence weights
   - Set up preferred symbols

---

## Support Resources

- **Documentation**: See README.md
- **API Docs**: http://localhost:8000/docs
- **Test Suite**: Run `python test_system.py`
- **Demo Script**: Run `python demo.py`

---

## Security Notes

⚠️ **Production Checklist:**

- [ ] Change default passwords
- [ ] Enable HTTPS/SSL
- [ ] Set up proper authentication
- [ ] Configure firewall rules
- [ ] Use environment variables for secrets
- [ ] Enable CORS only for trusted origins
- [ ] Regular security updates
- [ ] Monitor system logs

---

**Last Updated**: 2024
**Version**: 1.0.0
