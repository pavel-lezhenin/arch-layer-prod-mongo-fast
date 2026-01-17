# arch-layer-prod-mongo-fast

Production-ready layered architecture implementation with MongoDB, Redis, and Elasticsearch.

## 🏗️ Architecture Overview

This package demonstrates a **classic 3-tier layered architecture** designed for production use with a complete data stack:

```
┌──────────────────────────────────────┐
│     Presentation Layer (API)         │  FastAPI routes, HTTP handling
├──────────────────────────────────────┤
│     Business Logic Layer             │  Services, use cases, business rules
├──────────────────────────────────────┤
│     Data Access Layer                │  Repositories, data operations
├──────────────────────────────────────┤
│  Infrastructure (MongoDB + Redis +   │  Database, cache, search engine
│                 Elasticsearch)       │
└──────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. **Presentation Layer** (`api/`)
- FastAPI routes and endpoints
- Request/response validation
- HTTP error handling
- Dependency injection

#### 2. **Business Logic Layer** (`services/`)
- Core business rules
- Orchestrates repository calls
- Implements cache strategies
- Manages search indexing

#### 3. **Data Access Layer** (`repositories/`)
- **MongoRepository**: Primary data persistence (CRUD operations)
- **RedisRepository**: Caching layer with TTL
- **ElasticRepository**: Full-text search and advanced queries

#### 4. **Domain Layer** (`models/`)
- Pydantic models and schemas
- Beanie ODM documents
- Data validation rules

## ✨ Features

- ✅ **Strict layering** - Clear separation of concerns
- ✅ **Production stack** - MongoDB (data) + Redis (cache) + Elasticsearch (search)
- ✅ **Type safety** - 100% typed with mypy strict mode
- ✅ **Async/await** - Full async support for all I/O operations
- ✅ **Auto-caching** - Transparent caching with Redis
- ✅ **Search integration** - Automatic Elasticsearch indexing
- ✅ **Demo data** - Seed script with realistic product data
- ✅ **OpenAPI docs** - Auto-generated via FastAPI
- ✅ **80%+ test coverage** - Comprehensive test suite

## 📦 Installation

### Prerequisites

- Python 3.14+
- Docker & Docker Compose (for local development)

### Setup

1. **Install the package:**

```bash
cd packages/arch-layer-prod-mongo-fast
pip install -e '.[dev]'
```

2. **Start infrastructure services:**

```bash
docker compose up -d
```

This starts:
- **MongoDB** on `localhost:27017`
- **Redis** on `localhost:6379`
- **Elasticsearch** on `localhost:9200`
- **Kibana** on `localhost:5601` (for ES visualization)

3. **Configure environment:**

```bash
cp .env.example .env
# Edit .env if needed (defaults work with docker-compose)
```

4. **Seed demo data:**

```bash
python seed_data.py
```

This creates 12 sample products in MongoDB.

## 🚀 Usage

### Running the API

```bash
uvicorn arch_layer_prod_mongo_fast.main:app --reload
```

API available at: http://localhost:8000

OpenAPI docs: http://localhost:8000/docs

### API Endpoints

#### **Products CRUD**

```bash
# Create a product
POST /api/v1/products/
{
  "name": "Laptop Pro 15",
  "description": "High-performance laptop",
  "price": "1299.99",
  "stock": 25,
  "category": "Electronics"
}

# Get product by ID (cached after first fetch)
GET /api/v1/products/{product_id}

# Update product (invalidates cache)
PUT /api/v1/products/{product_id}
{
  "price": "1199.99",
  "stock": 30
}

# Delete product (removes from cache + search index)
DELETE /api/v1/products/{product_id}

# List products with filters
GET /api/v1/products/?category=Electronics&is_active=true&skip=0&limit=100
```

#### **Search Endpoints (Elasticsearch)**

```bash
# Full-text search
GET /api/v1/products/search/text?q=laptop&size=10

# Search by category
GET /api/v1/products/search/category/Electronics

# Search by price range
GET /api/v1/products/search/price?min_price=100&max_price=500
```

#### **Utility Endpoints**

```bash
# Reindex all products in Elasticsearch
POST /api/v1/products/reindex

# Clear all caches
DELETE /api/v1/products/cache

# Get product count
GET /api/v1/products/stats/count
```

### Demo Scenarios

#### Scenario 1: Cache Performance

```bash
# First request - hits MongoDB (slow)
time curl http://localhost:8000/api/v1/products/507f1f77bcf86cd799439011

# Second request - hits Redis cache (fast)
time curl http://localhost:8000/api/v1/products/507f1f77bcf86cd799439011
```

#### Scenario 2: Search vs Database

```bash
# Database query (exact match, slower for large datasets)
GET /api/v1/products/?category=Electronics

# Elasticsearch (fuzzy search, typo-tolerant, much faster)
GET /api/v1/products/search/text?q=electronik  # Finds "Electronics"
```

#### Scenario 3: Cache Invalidation

```bash
# Get product (caches result)
GET /api/v1/products/123

# Update product (cache automatically invalidated)
PUT /api/v1/products/123 { "price": "99.99" }

# Next GET fetches fresh data from MongoDB
GET /api/v1/products/123
```

## 📊 When to Use This Architecture

### ✅ **Use When:**

| Scenario | Reason |
|----------|--------|
| **CRUD-heavy applications** | Layered architecture excels at data operations |
| **Clear business logic** | Services layer handles complex workflows |
| **Need caching** | Redis integration for performance |
| **Search requirements** | Elasticsearch for full-text search |
| **Small to medium teams** | Simple, easy to understand |
| **MVP/Prototypes** | Fast development, proven pattern |
| **Microservices** | Each service can use this pattern |

### ❌ **Don't Use When:**

| Scenario | Better Alternative |
|----------|-------------------|
| **Complex domain models** | Use Clean/Hexagonal Architecture |
| **Event-driven systems** | Use CQRS/Event Sourcing |
| **High coupling concerns** | Use Ports & Adapters |
| **Multiple bounded contexts** | Use Modular Monolith |

## 💪 Strengths

1. **Simplicity** - Easy to learn, industry-standard pattern
2. **Fast development** - Clear structure accelerates coding
3. **Team onboarding** - Most developers familiar with pattern
4. **Production-ready** - Includes cache, search, monitoring
5. **Testability** - Each layer tested independently
6. **Scalability** - Horizontal scaling via Redis + Elasticsearch

## ⚠️ Weaknesses

1. **Tight coupling** - Layers depend on each other
2. **Anemic domain models** - Business logic in services, not models
3. **Database-centric** - Schema changes affect all layers
4. **Limited flexibility** - Hard to swap data sources
5. **Dependency flow** - Upper layers depend on lower (no inversion)

## 🔍 How Services Work Together

### Example: Creating a Product

```
1. API Layer (routes.py)
   ↓ Receives HTTP POST request
   ↓ Validates ProductCreate schema
   
2. Business Layer (product_service.py)
   ↓ create() method called
   ↓ Orchestrates:
   
3. Data Layer
   ├─→ MongoRepository: Saves to MongoDB
   └─→ ElasticRepository: Indexes in Elasticsearch
   
4. Response
   ↑ Returns Product model
   ↑ Converts to ProductResponse
   ↑ Returns 201 Created
```

### Example: Getting a Product (with Cache)

```
1. API Layer
   ↓ GET /api/v1/products/123
   
2. Business Layer
   ↓ get_by_id("123")
   
3. Cache Check
   ├─→ RedisRepository.get("product:123")
   │   ↓ Hit? Return cached data
   │   ↓ Miss? Continue...
   │
   ├─→ MongoRepository.get_by_id("123")
   │   ↓ Fetch from MongoDB
   │
   └─→ RedisRepository.set("product:123", data, ttl=300)
       ↓ Cache for 5 minutes
   
4. Response
   ↑ Return Product
```

## 🧪 Testing

Tests are organized into two categories:

### Test Structure

```
tests/
├── unit/                          # Fast tests with mocks
│   ├── test_api/                  # API route tests (mocked service)
│   ├── test_services/             # Service tests (mocked repositories)
│   ├── test_client.py            # HTTP client tests
│   ├── test_config.py            # Configuration tests
│   ├── test_exceptions.py        # Exception tests
│   └── test_models.py            # Model/schema tests
│
└── integration/                   # Slow tests with real containers
    ├── test_repositories/         # Repository tests (testcontainers)
    │   ├── test_mongo_repository.py
    │   ├── test_redis_repository.py
    │   └── test_elastic_repository.py
    └── test_main.py               # Application lifecycle tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests (fast, no Docker needed)
pytest tests/unit

# Run only integration tests (requires Docker)
pytest tests/integration

# Run with coverage
pytest --cov --cov-report=html
```

### Testing Philosophy

| Layer | Test Type | Uses |
|-------|-----------|------|
| API Routes | Unit | Mocked ProductService |
| Services | Unit | Mocked Repositories |
| Repositories | Integration | Testcontainers (real DB) |
| Models | Unit | Direct instantiation |

**Unit tests** are fast (~7s) and don't require Docker.
**Integration tests** use testcontainers to spin up real MongoDB, Redis, and Elasticsearch instances.

## 🛠️ Development

```bash
ruff check .      # Linting
ruff format .     # Formatting
mypy src          # Type checking
pytest tests/unit # Fast tests
bandit src        # Security scan
```

## 📂 Project Structure

```
src/arch_layer_prod_mongo_fast/
├── api/                      # PRESENTATION LAYER
│   ├── routes.py            # FastAPI endpoints
│   └── dependencies.py      # Dependency injection
│
├── services/                # BUSINESS LAYER
│   └── product_service.py   # Business logic + orchestration
│
├── repositories/            # DATA ACCESS LAYER
│   ├── mongo_repository.py  # MongoDB operations
│   ├── redis_repository.py  # Redis cache operations
│   └── elastic_repository.py # Elasticsearch operations
│
├── models/                  # DOMAIN LAYER
│   └── product.py          # Beanie documents + Pydantic schemas
│
├── config.py               # Settings (pydantic-settings)
├── exceptions.py           # Custom exceptions
└── main.py                # FastAPI app entry point

tests/
├── unit/                   # Fast tests (mocks)
│   ├── test_api/          # API route tests
│   ├── test_services/     # Service tests
│   ├── test_client.py     # HTTP client tests
│   ├── test_config.py     # Config tests
│   └── test_models.py     # Model tests
│
└── integration/           # Slow tests (testcontainers)
    ├── test_repositories/ # Repository tests
    │   ├── test_mongo_repository.py
    │   ├── test_redis_repository.py
    │   └── test_elastic_repository.py
    └── test_main.py       # Application lifecycle

compose.yml               # Infrastructure services
seed_data.py              # Demo data script
```

## 🔧 Configuration

All configuration via environment variables (see `.env.example`):

```bash
# Application
APP_TITLE=Layered Architecture Demo
APP_DEBUG=false

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=arch_layer_demo

# Redis
REDIS_URI=redis://localhost:6379/0
REDIS_CACHE_TTL=300  # 5 minutes

# Elasticsearch
ELASTICSEARCH_URI=http://localhost:9200
ELASTICSEARCH_INDEX=products
```

## 📋 Standards

- ✅ Strict typing (mypy strict)
- ✅ 80%+ test coverage
- ✅ Auto-formatting (ruff)
- ✅ Secret detection
- ✅ English only (code, comments, docs)
- ✅ Max 200 lines per file

---

**Built with:** FastAPI • MongoDB • Redis • Elasticsearch • Beanie • Pydantic

