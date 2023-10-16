# Python FastAPI Microservices

## Development
```bash
source env/bin/activate
pip install -i app/requirements.txt

uvicorn app.main:app --reload
```

Api: http://localhost:8000  
Docs: http://localhost:8000/docs

## Dockerized

### Up
```bash
docker compose -f docker/docker-compose.yaml up -d --build
```

### Down
```bash
docker compose -f docker/docker-compose.yaml up --rmi all --remove-orphans
```