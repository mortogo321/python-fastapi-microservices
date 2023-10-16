# Python FastAPI Microservices

## Development
```bash
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r app/requirements.txt

uvicorn app.main:app --reload
```

Api: http://localhost:8000  
Docs: http://localhost:8000/docs

## Dockerized

### Up
```bash
docker compose -f docker/docker-compose.development.yaml up -d --build
```

### Down
```bash
docker compose -f docker/docker-compose.development.yaml up --rmi all --remove-orphans
```