# Portfolio API

A FastAPI-based portfolio management system with authentication, real-time market data ETL, and portfolio tracking.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed

### Run the application

```bash
docker compose up --build
```

The API will be available at: http://localhost:8000

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Health Check
```bash
curl http://localhost:8000/healthz
```

## Project Structure

```
portfolio-api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database setup
│   ├── auth/                # Authentication module
│   ├── portfolio/           # Portfolio management
│   ├── etl/                 # ETL pipeline
│   └── core/                # Core utilities
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── docker-compose.yml       # Docker services
└── requirements.txt         # Python dependencies
```

## Development

### Stop the application
```bash
docker compose down
```

### View logs
```bash
docker compose logs -f api
```

### Run tests
```bash
docker compose exec api pytest
```

## Environment Variables

See `.env.example` for all configuration options.
