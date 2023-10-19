# Python FastAPI Microservices

## Development
```bash
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r app/requirements.txt
```

## RUN
```bash
# api
uvicorn app.api.main:app --reload --port=8000 --host=0.0.0.0

# payment
uvicorn app.payment.main:app --reload --port=8001 --host=0.0.0.0
```

Api: http://localhost:8000  
Payment: http://localhost:8001  
Docs: http://localhost:8000/docs

## Dockerized

### Up
```bash
docker compose -f docker/docker-compose.development.yaml up -d --build
```

### Down
```bash
docker compose -f docker/docker-compose.development.yaml down --rmi all --remove-orphans
```