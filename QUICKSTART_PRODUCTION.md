# CKD-CI Production Startup Guide

## Quick Start (One Command)

Start the entire system with one command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_production.ps1
```

This script will:
- ✓ Activate Python virtual environment
- ✓ Kill any existing processes on ports 8000 & 8501
- ✓ Run database migrations
- ✓ Create admin user (if needed)
- ✓ Start API Server (port 8000)
- ✓ Start Streamlit Dashboard (port 8501)
- ✓ Monitor both services and log everything

## What You Get

After running the script, the system will be available at:

| Component | URL | Purpose |
|-----------|-----|---------|
| **Streamlit Dashboard** | http://127.0.0.1:8501 | Web UI for predictions and analytics |
| **API Docs** | http://127.0.0.1:8000/docs | Interactive API documentation (Swagger) |
| **API ReDoc** | http://127.0.0.1:8000/redoc | Alternative API documentation |
| **Health Check** | http://127.0.0.1:8000/health | API status endpoint |

## Credentials

When you start the system for the first time, an admin user is automatically created:

```
Email: admin@example.com
Password: change_me
```

⚠️ **Change this password in production!**

## Before You Start

Make sure:
- ✓ Python 3.12+ is installed
- ✓ PostgreSQL database is running
- ✓ `.env` file is configured (copy from `.env.example` if needed)
- ✓ Virtual environment is set up: `.venv312/`
- ✓ Dependencies are installed (run `pip install -r requirements.txt` if needed)

## Running Only the API (without Streamlit)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_production.ps1 -NoStreamlit
```

## Running Custom Port

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_production.ps1 -ApiPort 9000 -StreamlitPort 9501
```

## Verify Everything Works

After the scripts start, run the integration test:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\local_fixup.ps1
```

This will:
- ✓ Test database connection
- ✓ Verify admin user
- ✓ Test authentication
- ✓ Register a test model
- ✓ Test prediction endpoint
- ✓ Check prediction history

## Health Check

Check system status anytime:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\health_check.ps1
```

## Logs

All output is logged to:
- **API Logs:** `./logs/api.log`
- **Streamlit Logs:** `./logs/streamlit.log`

View logs in real-time:
```powershell
Get-Content -Path .\logs\api.log -Wait
```

## Stopping the Services

When you see the running services, press **Ctrl+C** to stop them gracefully.

Or in another terminal:
```powershell
# Find and kill API process (port 8000)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Find and kill Streamlit process (port 8501)
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

## Docker Compose (Alternative)

For a fully containerized setup using Docker:

```bash
docker-compose up --build
```

Then access:
- Dashboard: http://localhost:8501
- API: http://localhost:8000

## Troubleshooting

### "Port 8000 already in use"
The script automatically cleans up old processes, but if it fails:
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### "ModuleNotFoundError"
Install requirements:
```powershell
python -m pip install -r requirements.txt
```

### "Database connection failed"
Verify PostgreSQL is running and `.env` is correct:
```powershell
cat .env  # Check DATABASE_URL
```

### "API starts but Streamlit doesn't load"
Streamlit takes 30-60 seconds on first start. Check logs:
```powershell
Get-Content .\logs\streamlit.log -Tail 50
```

## Architecture

```
┌─────────────────────────────────────────┐
│        Streamlit Dashboard              │
│        (Web UI on port 8501)            │
└─────────────┬───────────────────────────┘
              │
              │ HTTP Requests
              ↓
┌─────────────────────────────────────────┐
│        FastAPI Server                   │
│        (API on port 8000)               │
├─────────────────────────────────────────┤
│  • Authentication (JWT)                 │
│  • Prediction Engine                    │
│  • Model Registry                       │
│  • Monitoring & Metrics                 │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│      PostgreSQL Database                │
│    (Patient data, Predictions,          │
│     Models, Audit logs)                 │
└─────────────────────────────────────────┘
```

## Next Steps

After starting:

1. **Login to Dashboard**
   - Go to http://127.0.0.1:8501
   - Use credentials: admin@example.com / change_me

2. **Make a Prediction**
   - Enter patient information
   - Click "Run Prediction"
   - View results and confidence scores

3. **View Analytics**
   - Admin Analytics tab shows system metrics
   - Prediction History shows all past predictions

4. **Configure Models**
   - Use API docs (http://127.0.0.1:8000/docs)
   - Register new models
   - Promote models through stages (dev → staging → prod)

## Key Endpoints

### Authentication
- `POST /auth/login` - Get JWT token
- `POST /auth/logout` - Revoke token

### Predictions
- `POST /predictions/predict` - Single prediction
- `POST /predictions/batch` - Batch predictions
- `GET /predictions/history` - View past predictions

### Models
- `GET /models/` - List all models
- `GET /models/active` - Get active production model
- `POST /models/register` - Register new model
- `POST /models/promote` - Promote model to new stage
- `POST /models/deprecate` - Deprecate a model

### Monitoring
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Documentation

- Full API documentation: http://127.0.0.1:8000/docs
- Project README: [README.md](../README.md)
- Architecture guide: [SYSTEM_COMPLETE_GUIDE.md](../SYSTEM_COMPLETE_GUIDE.md)

---

**Questions?** Check the logs or review:
- `./logs/api.log` - API errors and traces
- `./logs/streamlit.log` - Dashboard errors
