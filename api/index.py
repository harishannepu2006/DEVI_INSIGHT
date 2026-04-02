from fastapi import FastAPI
import sys
import os
import traceback

# Add backend to path - verified folder visibility is [project_root]/backend
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_path = os.path.join(project_root, "backend")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Initialize the diagnostic app
app = FastAPI()
import_error = None

try:
    # Try to load the real production app
    from app.main import app as _app
    # Use the production app directly as our handler
    app = _app
except Exception as e:
    import_error = traceback.format_exc()
    print(f"CRITICAL: Backend import failed: {e}")

@app.get("/api/health-check")
@app.get("/health-check")
async def combined_health_v3():
    """Emergency diagnostic and standard health endpoint."""
    from app.config import settings
    from app.utils.supabase_client import get_db
    
    env_checks = {
        "SUPABASE_URL": bool(settings.SUPABASE_URL),
        "SUPABASE_SERVICE_ROLE_KEY": bool(settings.SUPABASE_SERVICE_ROLE_KEY),
        "GITHUB_TOKEN": bool(settings.GITHUB_TOKEN),
        "FRONTEND_URL": settings.FRONTEND_URL,
        "APP_ENV": settings.APP_ENV,
    }
    
    db_status = "UNKNOWN"
    db_error = None
    try:
        if env_checks["SUPABASE_URL"] and env_checks["SUPABASE_SERVICE_ROLE_KEY"]:
            db = get_db()
            db.table("users").select("count", count="exact").limit(1).execute()
            db_status = "CONNECTED"
        else:
            db_status = "MISSING_KEYS"
    except Exception as e:
        db_status = "ERROR"
        db_error = str(e)

    # Get all routes for debugging
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else None
        })

    if import_error:
        return {
            "status": "CRASHED",
            "detail": "Import failed",
            "traceback": import_error,
            "env_checks": env_checks,
            "db_status": db_status,
            "routes": routes
        }
    
    return {
        "status": "READY",
        "env_checks": env_checks,
        "db_status": db_status,
        "db_error": db_error,
        "routes": routes
    }

# Ensure Vercel finds the handler
handler = app
