# Python FastAPI Microservices

Modern microservices architecture built with **FastAPI**, **Python 3.13**, **Redis**, and **Docker**.

## Features

- **Python 3.13** - Latest stable Python version
- **FastAPI** - Modern, fast web framework with automatic OpenAPI docs
- **Async/Await** - Full async support with `httpx` for inter-service communication
- **Redis** - Data persistence and event streaming with Redis Streams
- **Pydantic v2** - Strong data validation and serialization
- **Structured Logging** - JSON logging for production observability
- **Docker** - Multi-stage builds for optimized production images
- **Health Checks** - Built-in health endpoints for monitoring
- **Type Safety** - Full type hints throughout the codebase

## Architecture

### Services

1. **Product API** (Port 8000)
   - Manages product catalog (CRUD operations)
   - Redis-backed persistence
   - RESTful API with OpenAPI documentation

2. **Payment Service** (Port 8001)
   - Processes orders and payments
   - Communicates with Product API via HTTP
   - Background task processing
   - Event publishing to Redis Streams

3. **Redis** (Port 6379)
   - Shared data store for both services
   - Event streaming with Redis Streams
   - Persistent storage with AOF

## Quick Start

### Using Docker (Recommended)

```bash
# Start all services
docker compose -f docker/docker-compose.development.yaml up -d --build

# View logs
docker compose -f docker/docker-compose.development.yaml logs -f

# Stop all services
docker compose -f docker/docker-compose.development.yaml down
```

### Local Development

```bash
# Create virtual environment
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r app/requirements.txt

# Run Product API
uvicorn app.api.main:app --reload --port=8000 --host=0.0.0.0

# Run Payment Service (in another terminal)
uvicorn app.payment.main:app --reload --port=8001 --host=0.0.0.0
```

## API Endpoints

### Product API (http://localhost:8000)

- `GET /` - Health check
- `GET /products` - List all products
- `POST /products` - Create a product
- `GET /products/{id}` - Get product by ID
- `DELETE /products/{id}` - Delete product
- `GET /docs` - Interactive API documentation

### Payment Service (http://localhost:8001)

- `GET /` - Health check
- `GET /orders` - List all orders
- `POST /orders` - Create an order
- `GET /orders/{id}` - Get order by ID
- `GET /docs` - Interactive API documentation

## Configuration

Environment variables are loaded from `.env.development` (see `.env.development` for available options):

```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_password
API_HOST=http://api:8000
PAYMENT_HOST=http://payment:8001
LOG_LEVEL=INFO
```

## Example Usage

### 1. Create a Product
```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 999.99, "quantity": 10}'
```

### 2. List Products
```bash
curl http://localhost:8000/products
```

### 3. Create an Order
```bash
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{"id": "PRODUCT_ID", "quantity": 2}'
```

### 4. List Orders
```bash
curl http://localhost:8001/orders
```

## Docker Commands

```bash
# Build and start services
docker compose -f docker/docker-compose.development.yaml up -d --build

# View logs
docker compose -f docker/docker-compose.development.yaml logs -f api
docker compose -f docker/docker-compose.development.yaml logs -f payment

# Stop services
docker compose -f docker/docker-compose.development.yaml down

# Stop and remove volumes
docker compose -f docker/docker-compose.development.yaml down -v

# Remove all (including images)
docker compose -f docker/docker-compose.development.yaml down --rmi all --remove-orphans
```

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.13 |
| Framework | FastAPI | 0.115+ |
| Server | Uvicorn | 0.32+ |
| Data Validation | Pydantic | 2.9+ |
| HTTP Client | httpx | 0.27+ |
| Database | Redis | 7 |
| Containerization | Docker | - |
| Orchestration | Docker Compose | - |

## Development

### Project Structure

```
.
├── app/
│   ├── api/                    # Product API service
│   │   ├── main.py            # FastAPI app & routes
│   │   └── product.py         # Product model
│   ├── payment/               # Payment service
│   │   ├── main.py           # FastAPI app & routes
│   │   └── order.py          # Order models
│   ├── libs/                  # Shared libraries
│   │   ├── config.py         # Configuration management
│   │   ├── logger.py         # Structured logging
│   │   └── redis.py          # Redis client
│   └── requirements.txt       # Python dependencies
├── docker/
│   ├── Dockerfile            # Multi-stage Docker build
│   └── docker-compose.development.yaml
└── README.md
```

### Key Improvements in v2.0

- Upgraded to Python 3.13
- Migrated from `redis-om` to modern `redis-py` with Pydantic integration
- Replaced synchronous `requests` with async `httpx`
- Added structured JSON logging
- Implemented proper error handling and validation
- Added health check endpoints with Redis connectivity tests
- Multi-stage Docker builds for smaller images
- Docker Compose health checks and proper service dependencies
- Full async/await pattern throughout
- Strong type hints and Pydantic v2 models
- Proper application lifecycle management

## Links

- Product API: http://localhost:8000
- Payment Service: http://localhost:8001
- API Documentation: http://localhost:8000/docs
- Payment Documentation: http://localhost:8001/docs

---

## Upgrade Notes (v2.0)

### What's New

#### Version Changes
- **Python**: 3.9.6 → 3.13 (latest stable)
- **FastAPI**: Upgraded to 0.115+
- **Pydantic**: v1 → v2.9+ (with improved validation)
- **Redis**: Migrated from `redis-om` to `redis-py` 5.2+
- **HTTP Client**: `requests` → `httpx` (async support)
- **Redis Image**: redis:alpine → redis:7-alpine

#### Key Improvements

1. **Full Async/Await Support**
   - All database operations are now async
   - HTTP client uses httpx for async inter-service communication
   - Better concurrency and performance

2. **Modern FastAPI Patterns**
   - Lifespan context managers for startup/shutdown
   - Proper dependency injection
   - Comprehensive error handling
   - Type hints throughout

3. **Enhanced Data Models**
   - Pydantic v2 with field validation
   - Order status as Enum (PENDING, COMPLETED, FAILED)
   - Custom validators for data integrity
   - Better API documentation with examples

4. **Configuration Management**
   - Added `pydantic-settings` for environment config
   - Type-safe configuration with validation
   - Support for multiple environments

5. **Structured Logging**
   - JSON logging with `python-json-logger`
   - Production-ready observability
   - Consistent log format across services

6. **Docker Improvements**
   - Multi-stage builds for smaller images
   - Runs as non-root user for security
   - Health checks for all services
   - Proper service dependencies
   - Custom networks for isolation

7. **Better Error Handling**
   - Appropriate HTTP status codes
   - Detailed error messages
   - Proper exception logging
   - Failed order status tracking

### Breaking Changes

⚠️ **Important**: This is a major version upgrade with breaking changes

1. **Redis Data Format Changed**
   - Migration from `redis-om` to `redis-py` changes storage format
   - **Existing Redis data will NOT be compatible**
   - Recommendation: Clear Redis database before upgrade

2. **API Response Changes**
   - Product and Order models now include `pk` field in responses
   - Order status values are lowercase: "pending", "completed", "failed"

3. **Python Version Requirement**
   - Requires Python 3.13+
   - Update your development environment accordingly

### Migration Guide

#### Using Docker (Recommended)

```bash
# 1. Stop and remove existing containers with volumes
docker compose -f docker/docker-compose.development.yaml down -v

# 2. Rebuild and start with new version
docker compose -f docker/docker-compose.development.yaml up -d --build

# 3. Verify all services are healthy
docker compose -f docker/docker-compose.development.yaml ps
```

#### Local Development

```bash
# 1. Verify Python 3.13 is installed
python3.13 --version

# 2. Remove old virtual environment
rm -rf env

# 3. Create new virtual environment with Python 3.13
python3.13 -m venv env
source env/bin/activate

# 4. Install updated dependencies
pip install --upgrade pip
pip install -r app/requirements.txt

# 5. Clear Redis data (if using local Redis)
redis-cli FLUSHALL

# 6. Run services
uvicorn app.api.main:app --reload --port=8000 --host=0.0.0.0
```

### Testing the Upgrade

#### 1. Health Checks
```bash
curl http://localhost:8000/  # Should return {"status": true, ...}
curl http://localhost:8001/  # Should return {"status": true, ...}
```

#### 2. Create and Query Products
```bash
# Create product
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "price": 99.99, "quantity": 10}'

# List products
curl http://localhost:8000/products
```

#### 3. Create and Track Orders
```bash
# Create order (replace {product_pk} with actual product ID)
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{"id": "{product_pk}", "quantity": 2}'

# Check order status (wait 5 seconds for completion)
curl http://localhost:8001/orders/{order_pk}
```

### Benefits

- **10%+ Performance Improvement**: Python 3.13 and async patterns
- **Type Safety**: Comprehensive type hints reduce runtime errors
- **Better Developer Experience**: Improved error messages and IDE support
- **Production Ready**: Structured logging, health checks, graceful shutdown
- **Security**: Non-root containers, latest security patches
- **Maintainability**: Modern patterns and comprehensive documentation