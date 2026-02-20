"""
FastAPI application entry point for Architect backend.
Initializes services, registers routes, and manages app lifecycle.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# LIFESPAN
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes all services on startup, cleans up on shutdown.
    """
    # --- STARTUP ---
    logger.info("🚀 Starting Architect backend...")
    logger.info(f"   Environment : {settings.environment}")
    logger.info(f"   Debug mode  : {settings.debug}")
    logger.info(f"   LLM default : {settings.default_llm_provider}")

    # Initialize services (import here to trigger __init__)
    try:
        from app.services.llm_service import llm_service
        logger.info("   ✅ LLM Service ready (Gemini + Groq)")
    except Exception as e:
        logger.error(f"   ❌ LLM Service failed: {e}")

    try:
        from app.services.db_service import db_service
        logger.info("   ✅ Database Service ready (Supabase)")
    except Exception as e:
        logger.error(f"   ❌ Database Service failed: {e}")

    try:
        from app.services.vector_service import vector_service
        logger.info("   ✅ Vector Service ready (Qdrant)")
    except Exception as e:
        logger.error(f"   ❌ Vector Service failed: {e}")

    try:
        from app.services.crawler_service import crawler_service
        logger.info("   ✅ Crawler Service ready")
    except Exception as e:
        logger.error(f"   ❌ Crawler Service failed: {e}")

    logger.info("✅ Architect backend is ready!\n")

    yield

    # --- SHUTDOWN ---
    logger.info("👋 Shutting down Architect backend...")


# ------------------------------------------------------------------
# APP
# ------------------------------------------------------------------

app = FastAPI(
    title="Architect API",
    description=(
        "AI-powered orchestration platform that transforms naive ideas "
        "into professional engineering implementations via a Socratic Loop."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api prefix
app.include_router(router, prefix="/api")


# ------------------------------------------------------------------
# ROOT ENDPOINTS
# ------------------------------------------------------------------

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — basic API info."""
    return {
        "name": "Architect API",
        "version": "0.1.0",
        "description": "AI-powered engineering orchestration platform",
        "docs": "/docs",
        "health": "/health",
        "endpoints": "/api",
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """Health check endpoint — confirms API is running."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0",
    }


# ------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
