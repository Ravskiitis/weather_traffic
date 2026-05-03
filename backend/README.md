# weather_traffic — Backend

FastAPI backend for the weather/traffic dashboard.

## Run locally

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Copy the env template and fill in values
cp ../.env.example ../.env
# Edit ../.env — at minimum set ANTHROPIC_API_KEY

# 4. Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `curl http://localhost:8000/api/health`

## Code quality

```bash
ruff check app/
ruff format app/
pytest
```
