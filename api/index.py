from fastapi import FastAPI
import sys
import os
import traceback

# Add backend to path - verified folder visibility is [project_root]/backend
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_path = os.path.join(project_root, "backend")

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Initialize a fallback app in case the import fails
app = FastAPI()
import_error = None

try:
    # Try to load the real production app
    from app.main import app as _app
    app = _app
except Exception as e:
    import_error = traceback.format_exc()
    print(f"CRITICAL: Backend import failed: {e}")

@app.get("/api/health-check")
async def combined_health():
    """Emergency diagnostic and standard health endpoint."""
    if import_error:
        return {
            "status": "CRASHED",
            "detail": "The backend failed to load. Check traceback below.",
            "traceback": import_error,
            "sys_path": sys.path,
            "project_root": project_root
        }
    return {
        "status": "READY",
        "message": "DevInsight API is active and reconnected",
        "project_root": project_root,
        "backend_path": backend_path
    }

# Ensure Vercel finds the handler
handler = app
