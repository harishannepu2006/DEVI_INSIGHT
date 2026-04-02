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
async def combined_health_v2():
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
            # Simple query to check connectivity and schema
            db.table("users").select("count", count="exact").limit(1).execute()
            db_status = "CONNECTED"
        else:
            db_status = "MISSING_KEYS"
    except Exception as e:
        db_status = "ERROR"
        db_error = str(e)

    if import_error:
        return {
            "status": "CRASHED",
            "detail": "The backend failed to load. Check traceback below.",
            "traceback": import_error,
            "sys_path": sys.path,
            "project_root": project_root,
            "env_checks": env_checks,
            "db_status": db_status,
            "db_error": db_error
        }
    
    return {
        "status": "READY",
        "message": "DevInsight API is active and reconnected",
        "project_root": project_root,
        "backend_path": backend_path,
        "env_checks": env_checks,
        "db_status": db_status,
        "db_error": db_error
    }

# Ensure Vercel finds the handler
handler = app
