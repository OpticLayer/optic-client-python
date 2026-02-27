# Optic Python SDK

Auto-instrument your Python application with **one line of code** — just like Datadog's `ddtrace`.

## Quick Start

```bash
pip install -e ./optic-sdk
```

```python
import optic

optic.init(
    api_key="your-team-api-key",
    service_name="my-app",
    endpoint="http://localhost:8080",  # optional
)

# That's it! Traces, metrics, and logs are automatically collected.
```

## What Gets Collected

### Traces
- HTTP requests (Flask, Django, FastAPI)
- Outgoing HTTP calls (requests, urllib3, httpx)
- Database queries (SQLAlchemy, PyMySQL, psycopg2)
- Redis operations
- Celery tasks

### Metrics
- System: CPU, memory, disk utilization
- Application: Request count, duration, errors (via instrumented frameworks)

### Logs
- Python `logging` module automatically bridged to OTel logs
- Correlated with trace context (trace_id, span_id)

## Configuration

All settings can be passed to `init()` or set via env vars:

| `init()` kwarg | Env Var | Default | Description |
|----------------|---------|---------|-------------|
| `api_key` | `OPTIC_API_KEY` | — | Team API key (required) |
| `service_name` | `OPTIC_SERVICE_NAME` | — | Service name (required) |
| `endpoint` | `OPTIC_ENDPOINT` | `http://localhost:8080` | Backend URL |
| `environment` | `OPTIC_ENVIRONMENT` | `local` | Deployment environment |
| `service_version` | `OPTIC_SERVICE_VERSION` | — | Version tag |

### Optional Features

```python
optic.init(
    api_key="...",
    service_name="...",
    auto_instrument=True,         # Auto-detect & instrument libraries
    enable_traces=True,           # Collect traces
    enable_metrics=True,          # Collect metrics
    enable_logs=True,             # Capture Python logs
    enable_system_metrics=True,   # CPU/memory/disk metrics
    log_level="INFO",             # Min log level to capture
    excluded_urls=["/health"],    # URLs to skip tracing
)
```

## Framework Examples

### Flask

```python
import optic
optic.init(api_key="...", service_name="my-flask-app")

from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World"  # Automatically traced!
```

### FastAPI

```python
import optic
optic.init(api_key="...", service_name="my-fastapi-app")

from fastapi import FastAPI
app = FastAPI()

@app.get("/")
async def hello():
    return {"message": "Hello World"}  # Automatically traced!
```
