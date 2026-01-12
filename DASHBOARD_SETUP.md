# Dashboard Setup Guide

## Problem Solved

The glossary page was not displaying because **Flask dependencies were not installed**.

## Root Cause Analysis

1. **Symptom**: Accessing `/glossary` resulted in no response or error
2. **Investigation**:
   - ✅ HTML file exists: `glossary.html` (58KB, valid HTML)
   - ✅ Route exists: `/glossary`, `/glossaire`, `/glossary.html` in `dashboard_api.py`
   - ❌ **Flask module not installed** - `ModuleNotFoundError: No module named 'flask'`

3. **Solution**: Install Flask and Flask-CORS dependencies

## Quick Start

### Option 1: Use the Startup Script (Recommended)
```bash
# Windows
start_dashboard.bat

# Linux/Mac
chmod +x start_dashboard.sh
./start_dashboard.sh
```

### Option 2: Manual Start
```bash
# Install dependencies
pip install flask flask-cors

# Start server
python dashboard_api.py
```

## Access the Dashboard

Once the server is running:

- **Dashboard**: http://localhost:5000/
- **Glossary**: http://localhost:5000/glossary
- **Compare**: http://localhost:5000/compare.html

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/alerts` - List alerts with filters
- `GET /api/stats` - Global statistics
- `GET /api/networks` - Network statistics
- `GET /api/alerts/:id` - Alert details
- `GET /api/recent` - Recent alerts

## Production Deployment

For production (Railway, etc.), the server automatically:
- Uses `PORT` environment variable
- Detects `RAILWAY_ENVIRONMENT`
- Serves from `/data/alerts_history.db` if available
- Disables debug mode

## Troubleshooting

### Flask not installed
```bash
pip install flask flask-cors
```

### Port already in use
Change the port in `dashboard_api.py`:
```python
port = int(os.environ.get('PORT', 5000))  # Change 5000 to another port
```

### Database not found
The API will still serve HTML pages even if the database is missing.
API endpoints will return errors until the scanner creates the database.

## Files Structure

```
bot-market/
├── dashboard_api.py          # Flask API server (PORT 5000)
├── dashboard_frontend.html   # Main dashboard page
├── glossary.html            # Glossary/guide page
├── compare.html             # Comparison page
├── start_dashboard.bat      # Windows startup script
├── requirements.txt         # Python dependencies
└── alerts_history.db        # SQLite database (created by scanner)
```

## Dependencies

From `requirements.txt`:
```
flask==3.0.0
flask-cors==4.0.0
```

## Fix Applied: January 12, 2026

✅ Flask and Flask-CORS installed
✅ Server tested and working
✅ Glossary page accessible at http://localhost:5000/glossary
✅ Startup script created for easy server start
