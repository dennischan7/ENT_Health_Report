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

### AI Configurations (Admin only)

```
GET    /api/ai-configs              - List AI configurations
GET    /api/ai-configs/{id}         - Get AI configuration
POST   /api/ai-configs              - Create AI configuration
PUT    /api/ai-configs/{id}         - Update AI configuration
DELETE /api/ai-configs/{id}         - Delete AI configuration
POST   /api/ai-configs/{id}/activate - Activate AI configuration
```

### Reports

```
POST   /api/reports/generate                    - Start report generation
GET    /api/reports/{task_id}/status            - Get task status
GET    /api/reports/{task_id}/download          - Download report
GET    /api/reports                             - List reports
GET    /api/reports/{report_id}                 - Get report detail
DELETE /api/reports/{task_id}                   - Cancel/delete task
GET    /api/reports/enterprises/{id}/summary    - Enterprise report summary
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
| Phase 0 | Infrastructure setup | ✅ Completed |
| Phase 1 | Core framework (auth, users) | ✅ Completed |
| Phase 2 | Enterprise data management | ✅ Completed |
| Phase 3 | Indicator calculation engine | ✅ Completed |
| Phase 4 | AI report generation | ✅ Completed |
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

## AI Configuration Commands

### Manage AI Configurations

```bash
# List all AI configurations
curl -X GET http://localhost:8005/api/ai-configs \
  -H "Authorization: Bearer <token>"

# Create a new AI configuration (admin only)
curl -X POST http://localhost:8005/api/ai-configs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "config_name": "DeepSeek-Production",
    "provider": "deepseek",
    "api_key": "sk-xxx",
    "model_name": "deepseek-chat",
    "is_default": true
  }'

# Update an AI configuration (admin only)
curl -X PUT http://localhost:8005/api/ai-configs/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "deepseek-coder",
    "temperature": 0.5
  }'

# Activate an AI configuration (admin only)
curl -X POST http://localhost:8005/api/ai-configs/1/activate \
  -H "Authorization: Bearer <token>"

# Delete an AI configuration (admin only)
curl -X DELETE http://localhost:8005/api/ai-configs/1 \
  -H "Authorization: Bearer <token>"
```

### Supported AI Providers

| Provider | Identifier | Notes |
|----------|------------|-------|
| OpenAI | `openai` | GPT-4, GPT-3.5 |
| DeepSeek | `deepseek` | OpenAI-compatible |
| Qwen | `qwen` | Alibaba, OpenAI-compatible |
| Kimi | `kimi` | Moonshot AI |
| MiniMax | `minimax` | OpenAI-compatible |
| Gemini | `gemini` | Google AI |
| GLM | `glm` | ZhipuAI |
| OpenAI-Compatible | `openai-compatible` | Custom endpoints |

---

## Report Generation Commands

### Generate and Manage Reports

```bash
# Start report generation
curl -X POST http://localhost:8005/api/reports/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "enterprise_id": 1,
    "report_type": "full_diagnosis",
    "report_years": "2021-2023",
    "include_peer_comparison": true,
    "peer_count": 5
  }'

# Check task status
curl -X GET http://localhost:8005/api/reports/{task_id}/status \
  -H "Authorization: Bearer <token>"

# Download completed report
curl -X GET http://localhost:8005/api/reports/{task_id}/download \
  -H "Authorization: Bearer <token>" \
  -o report.docx

# List all reports
curl -X GET "http://localhost:8005/api/reports?page=1&page_size=20" \
  -H "Authorization: Bearer <token>"

# Cancel running task
curl -X DELETE http://localhost:8005/api/reports/{task_id} \
  -H "Authorization: Bearer <token>"
```

### Report Types

- `full_diagnosis` - Complete health diagnosis report
- `quick_diagnosis` - Quick diagnostic summary
- `financial_analysis` - Financial metrics analysis
- `risk_assessment` - Risk identification and evaluation

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

### AI configuration issues

```bash
# Check if AI configs exist in database
docker-compose exec postgres-kimi psql -U health_user -d health_db_kimi \
  -c "SELECT id, config_name, provider, is_active, is_default FROM ai_configs;"

# Check if an AI config is active
docker-compose exec postgres-kimi psql -U health_user -d health_db_kimi \
  -c "SELECT * FROM ai_configs WHERE is_active = true;"

# View AI config audit logs
docker-compose exec postgres-kimi psql -U health_user -d health_db_kimi \
  -c "SELECT * FROM ai_config_audit_logs ORDER BY created_at DESC LIMIT 10;"
```

### Report generation issues

```bash
# Check report task status in database
docker-compose exec postgres-kimi psql -U health_user -d health_db_kimi \
  -c "SELECT id, task_id, status, error_message FROM generated_reports ORDER BY created_at DESC LIMIT 5;"

# View backend logs for report errors
docker-compose logs backend-kimi | grep -i "report\|llm\|error"

# Check Redis for task queue status
docker-compose exec redis-kimi redis-cli KEYS "report:*"
```

### LLM API connection issues

1. **API Key 验证失败**
   - 确认 API Key 格式正确（通常以 `sk-` 开头）
   - 检查 API Key 是否有效且未过期
   - 确认账户余额充足

2. **网络连接超时**
   - 检查服务器网络是否可访问 LLM API 地址
   - 如在国内使用 OpenAI，可能需要配置代理或使用 OpenAI-Compatible 提供商

3. **模型不存在错误**
   - 确认模型名称正确（如 `gpt-4`、`deepseek-chat`）
   - 不同提供商支持的模型名称不同

4. **配置未激活**
   - 创建配置后需要点击「激活」按钮
   - 同一时间只能有一个活跃配置

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