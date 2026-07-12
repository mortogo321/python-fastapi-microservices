# Python FastAPI Microservices

A small microservices sample demonstrating service boundaries, async inter-service HTTP calls, event publishing, and background job processing with FastAPI.

## What's Inside

- **Product API** — FastAPI service exposing CRUD endpoints for a product catalog, backed by Redis.
- **Payment Service** — FastAPI service that creates orders, calls the Product API over HTTP to validate and price them, completes orders asynchronously via a background task, and publishes an `order_completed` event to a Redis stream.
- **Redis** — Shared data store for both services (hash-based model persistence) and the transport for the order-completion event stream.

## Tech Stack

- Python 3.13, FastAPI, Pydantic v2 (`pydantic-settings` for config)
- Uvicorn ASGI server
- `httpx` for async inter-service HTTP calls
- Redis (`redis-py` async client) for persistence and Redis Streams
- Structured JSON logging (`python-json-logger`)
- Docker multi-stage build, Docker Compose orchestration

## Quickstart

```bash
docker compose -f docker/docker-compose.development.yaml up -d --build
```

- Product API: http://localhost:8000/docs
- Payment Service: http://localhost:8001/docs

Or run locally without Docker:

```bash
python3 -m venv env
source env/bin/activate
pip install -r app/requirements.txt

# in separate terminals
uvicorn app.api.main:app --reload --port=8000
uvicorn app.payment.main:app --reload --port=8001
```

A local Redis instance and a `.env` file (see `.env.development`) are required for local runs.

### Example requests

```bash
# Create a product
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 999.99, "quantity": 10}'

# Order it (payment service fetches the product from the API and processes the order in the background)
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{"id": "<product_id>", "quantity": 2}'
```

## Structure

```
app/
├── api/          # Product API service (main.py, product.py)
├── payment/      # Payment service (main.py, order.py)
├── libs/         # Shared config, structured logging, and Redis client
└── requirements.txt
docker/
├── Dockerfile
└── docker-compose.development.yaml
```
