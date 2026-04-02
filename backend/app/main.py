"""DevInsight — Code Quality Intelligence Platform.

FastAPI application entry point.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, repositories, analysis, bugs, insights, reports, chat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DevInsight API",
    description="AI-powered Code Quality Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "https://deviinsight.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# --- CENTRALIZED ROUTING TABLE ---
# We explicitly map each router to its final /api address.
# This eliminates all ambiguity and ensures 100% Vercel compatibility.

app.include_router(auth.router, prefix="/api/auth")
app.include_router(repositories.router, prefix="/api/repositories")
app.include_router(analysis.router, prefix="/api/analysis")
app.include_router(bugs.router, prefix="/api/bugs")
app.include_router(insights.router, prefix="/api/insights")
app.include_router(reports.router, prefix="/api/reports")
app.include_router(chat.router, prefix="/api/chat")

@app.get("/api/health")
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "DevInsight API is active"}

@app.get("/api/health/debug")
async def health_debug():
    """Diagnostic endpoint to check environment variables (masked)."""
    from app.config import settings
    return {
        "status": "active",
        "env": settings.APP_ENV,
        "checks": {
            "SUPABASE_URL": bool(settings.SUPABASE_URL),
            "SUPABASE_SERVICE_ROLE_KEY": bool(settings.SUPABASE_SERVICE_ROLE_KEY),
            "GITHUB_TOKEN": bool(settings.GITHUB_TOKEN),
            "SECRET_KEY": settings.SECRET_KEY != "devinsight-secret-key-change-in-production"
        }
    }

# --- Static File Hosting for Frontend ---
# This serves the React build directory (static files)
# Ensure the folder exists to avoid startup errors
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="static")

    # Catch-all route to serve index.html for React Router (Single Page Application)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Exclude API calls from the catch-all
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc"):
            return None
        
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend not built yet. Run 'npm run build' in the frontend folder."}
else:
    @app.get("/")
    async def root():
        """Root endpoint fallback."""
        return {
            "name": "DevInsight API",
            "version": "1.0.0",
            "description": "AI-powered Code Quality Platform",
            "docs": "/api/docs",
            "frontend_status": "Static directory not found. Please build frontend first."
        }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "devinsight-api"}


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info(f"🔷 DevInsight API starting in {settings.APP_ENV} mode")
    logger.info(f"📍 Frontend URL: {settings.FRONTEND_URL}")
    logger.info(f"📍 Backend URL: {settings.BACKEND_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown cleanup."""
    logger.info("🔷 DevInsight API shutting down")
