# Quick Start Guide

## Start the Stack

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Install package
pip install -e '.[dev]'

# 3. Seed demo data
python seed_data.py

# 4. Run API server
uvicorn arch_layer_prod_mongo_fast.main:app --reload
```

## Test the API

```bash
# Health check
curl http://localhost:8000/health

# Create a product
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Product",
    "description": "Demo product",
    "price": "99.99",
    "stock": 100,
    "category": "Test"
  }'

# List all products
curl http://localhost:8000/api/v1/products/

# Search with Elasticsearch
curl "http://localhost:8000/api/v1/products/search/text?q=laptop"
```

## Check Services

- **API Docs**: http://localhost:8000/docs
- **Kibana**: http://localhost:5601
- **MongoDB**: mongodb://localhost:27017
- **Redis**: redis://localhost:6379
- **Elasticsearch**: http://localhost:9200

## Run Tests

```bash
pytest -v
```

## Architecture Layers

```
📁 api/           → FastAPI routes (Presentation)
📁 services/      → Business logic
📁 repositories/  → Data access (Mongo, Redis, Elastic)
📁 models/        → Domain models (Pydantic + Beanie)
```

## Key Files

- `main.py` - FastAPI app entry point
- `config.py` - Environment configuration
- `seed_data.py` - Demo data generator
- `compose.yml` - Infrastructure stack
