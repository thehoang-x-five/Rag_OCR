"""
FastAPI OCR Service - Main application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.jobs import job_store
from app.api import routes_ocr, routes_convert, routes_jobs, routes_rag

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting OCR Service...")
    logger.info(f"Storage directory: {settings.STORAGE_DIR}")
    logger.info(f"Default parser: {settings.DEFAULT_PARSER}")
    logger.info(f"RAG enabled: {settings.ENABLE_RAG}")
    
    # Create storage directory
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    yield
    
    logger.info("Shutting down OCR Service...")
    # Cleanup jobs
    job_store.cleanup_all()


app = FastAPI(
    title="RAG-Anything OCR Service",
    description="OCR and document processing service with optional RAG capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_ocr.router, prefix="/api/ocr", tags=["OCR"])
app.include_router(routes_convert.router, prefix="/api/convert", tags=["Convert"])
app.include_router(routes_jobs.router, prefix="/api/jobs", tags=["Jobs"])

if settings.ENABLE_RAG:
    app.include_router(routes_rag.router, prefix="/api/rag", tags=["RAG"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    from app.core.ollama_client import check_ollama_connection
    
    ollama_reachable = False
    if settings.ENABLE_RAG:
        try:
            ollama_reachable = await check_ollama_connection()
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
    
    # Check AI provider status
    ai_providers_status = {}
    if settings.AI_ENHANCEMENT_ENABLED:
        try:
            from app.core.ai_providers.provider_manager import provider_manager
            provider_statuses = await provider_manager.get_provider_status()
            
            for name, status in provider_statuses.items():
                ai_providers_status[name] = {
                    "available": status.available,
                    "responseTimeMs": status.response_time_ms,
                    "supportsVision": status.supports_vision,
                    "quotaExceeded": status.quota_exceeded,
                    "unavailableReason": status.unavailable_reason
                }
        except Exception as e:
            logger.warning(f"Could not get AI provider status: {e}")
    
    return {
        "ok": True,
        "version": "1.0.0",
        "parserDefault": settings.DEFAULT_PARSER,
        "enableRag": settings.ENABLE_RAG,
        "ollamaReachable": ollama_reachable,
        "aiEnhancementEnabled": settings.AI_ENHANCEMENT_ENABLED,
        "aiProviders": ai_providers_status if ai_providers_status else None
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.APP_ENV == "dev" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_ENV == "dev"
    )