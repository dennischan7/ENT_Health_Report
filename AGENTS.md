# Enterprise Health Report - Development Guide

## Project Overview

Enterprise Health Diagnosis Platform (企业健康度智能诊断平台) - An intelligent system for automating enterprise diagnosis workflows.

### Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11 + FastAPI |
| Frontend | React 18 + TypeScript + Vite |
| UI Library | Ant Design 5.x |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Charts | ECharts 5.x |
| Deployment | Docker Compose |

### Project Structure

```
ENT_Health_Report-kimi2.5/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── core/              # Config, security, logging
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # API routes
│   │   ├── db/                # Database session
│   │   └── services/          # Business logic
│   ├── tests/                 # Test suite
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom hooks
│   │   ├── lib/               # Utilities, API client
│   │   ├── types/             # TypeScript types
│   │   └── styles/            # Global styles
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docker-compose.yml          # Docker orchestration
├── .env.example               # Environment template
└── AGENTS.md                  # This file
```

---

## Docker Services (kimi version)

| Service | Container Name | Port | Internal Port |
|---------|----------------|------|---------------|
| PostgreSQL | ent-health-postgres-kimi | 5437 | 5432 |
| Redis | ent-health-redis-kimi | 6384 | 6379 |
| Backend | ent-health-backend-kimi | 8005 | 8000 |
| Frontend | ent-health-frontend-kimi | 3005 | 3000 |

---

## Build Commands

### Backend

```bash
# Install dependencies (in Docker)
docker-compose exec backend-kimi pip install -r requirements.txt

# Run development server (in Docker)
docker-compose exec backend-kimi uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run locally (without Docker)
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8005
```

### Frontend

```bash
# Install dependencies (in Docker)
docker-compose exec frontend-kimi npm install

# Run development server (in Docker)
docker-compose exec frontend-kimi npm run dev

# Run locally (without Docker)
cd frontend
npm install
npm run dev
```

---

## Test Commands

### Backend Tests

```bash
# Run all tests
docker-compose exec backend-kimi pytest

# Run with coverage
docker-compose exec backend-kimi pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec backend-kimi pytest tests/test_auth.py -v

# Run locally
cd backend
pytest
```

### Frontend Tests

```bash
# Run tests
docker-compose exec frontend-kimi npm run test

# Run locally
cd frontend
npm run test
```

---

## Lint Commands

### Backend (Ruff + Black)

```bash
# Check code style
docker-compose exec backend-kimi ruff check app/

# Format code
docker-compose exec backend-kimi black app/

# Run locally
cd backend
ruff check app/
black app/
```

### Frontend (ESLint)

```bash
# Check code
docker-compose exec frontend-kimi npm run lint

# Fix issues
docker-compose exec frontend-kimi npm run lint -- --fix

# Run locally
cd frontend
npm run lint
```

---

## Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend-kimi
docker-compose logs -f frontend-kimi

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up -d --build

# Check service status
docker-compose ps

# Execute command in container
docker-compose exec backend-kimi bash
docker-compose exec frontend-kimi sh

# Access PostgreSQL
docker-compose exec postgres-kimi psql -U health_user -d health_db_kimi

# Access Redis
docker-compose exec redis-kimi redis-cli
```

---

## Database Commands

```bash
# Run migrations (Phase 1+)
docker-compose exec backend-kimi alembic upgrade head

# Create migration
docker-compose exec backend-kimi alembic revision --autogenerate -m "description"

# Rollback migration
docker-compose exec backend-kimi alembic downgrade -1

# Query database
docker-compose exec postgres-kimi psql -U health_user -d health_db_kimi -c "SELECT * FROM users;"
```

---

## API Endpoints (Phase 1+)

### Health Check

```
GET /health
Response: { "status": "ok", "service": "backend-kimi", "version": "1.0.0" }
```

### Authentication

```
POST /api/auth/login     - User login
POST /api/auth/logout    - User logout
GET  /api/auth/me        - Get current user
POST /api/auth/refresh   - Refresh token
```

### Users (Admin only)

```
GET    /api/users        - List users
GET    /api/users/{id}   - Get user
POST   /api/users        - Create user
PUT    /api/users/{id}   - Update user
DELETE /api/users/{id}   - Delete user
```

### Enterprises

```
GET    /api/enterprises        - List enterprises
GET    /api/enterprises/{id}   - Get enterprise
POST   /api/enterprises        - Create enterprise
PUT    /api/enterprises/{id}   - Update enterprise
DELETE /api/enterprises/{id}   - Delete enterprise
```

---

## Code Style Guidelines

### Python (Backend)

- Use **Black** for formatting (line length: 100)
- Use **Ruff** for linting
- Use **type hints** for all functions
- Use **Pydantic** for data validation
- Use **SQLAlchemy 2.0** style with `DeclarativeBase`

```python
# Example
from typing import Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
```

### TypeScript (Frontend)

- Use **ESLint** for linting
- Use **functional components** with hooks
- Use **TypeScript interfaces** for types
- Use **Ant Design** components

```typescript
// Example
interface User {
  id: number;
  email: string;
  fullName?: string;
}

const LoginPage: React.FC = () => {
  // Component logic
};
```

---

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Infrastructure setup | ✅ Current |
| Phase 1 | Core framework (auth, users) | ⏳ Pending |
| Phase 2 | Enterprise data management | ⏳ Pending |
| Phase 3 | Indicator calculation engine | ⏳ Pending |
| Phase 4 | AI report generation | ⏳ Pending |
| Phase 5 | Historical data & optimization | ⏳ Pending |

---

## Environment Variables

See `.env.example` for all available variables:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key
- `CORS_ORIGINS` - Allowed CORS origins
- `LLM_API_BASE_URL` - LLM API endpoint (Phase 4)
- `LLM_API_KEY` - LLM API key (Phase 4)

---

## Troubleshooting

### Port conflicts

Check if ports are already in use:
```bash
# Windows
netstat -ano | findstr :5437
netstat -ano | findstr :6384
netstat -ano | findstr :8005
netstat -ano | findstr :3005
```

### Database connection issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres-kimi

# Check PostgreSQL logs
docker-compose logs postgres-kimi

# Test connection
docker-compose exec postgres-kimi pg_isready -U health_user
```

### Frontend build issues

```bash
# Clear node_modules and reinstall
docker-compose exec frontend-kimi sh -c "rm -rf node_modules && npm install"
```

---

## Useful Links

- FastAPI Docs: http://localhost:8005/docs
- ReDoc: http://localhost:8005/redoc
- Frontend: http://localhost:3005
- Health Check: http://localhost:8005/health

---

## Notes

- This is the **kimi** version of the project with port offsets (+5)
- Default admin credentials: `admin@example.com` / `admin123` (Phase 1)
- All Docker resources are named with `-kimi` suffix to avoid conflicts