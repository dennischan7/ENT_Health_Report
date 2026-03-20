"""
FastAPI Application Entry Point.
Enterprise Health Report - Backend API
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.session import engine
from app.db.base import Base

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events handler."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    # Create initial admin user
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.core.security import get_password_hash

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                full_name="管理员",
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Initial admin user created: admin@example.com")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
    finally:
        db.close()

    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Health Diagnosis Platform Backend API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "ok", "service": "backend-kimi", "version": settings.APP_VERSION}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {"message": f"Welcome to {settings.APP_NAME}", "docs": "/docs", "health": "/health"}


# Include routers
from app.api import auth, users, enterprises, financials

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(enterprises.router, prefix="/api/enterprises", tags=["Enterprises"])
app.include_router(financials.router, prefix="/api/financials", tags=["Financials"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8005, reload=True)
