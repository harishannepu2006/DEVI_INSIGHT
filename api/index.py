import sys
import os
from fastapi import FastAPI

# Hardened Path Resolution
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(base_dir, "backend")

if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Initialize app as a minimal fallback first to prevent "Could not find app" errors
app = FastAPI()

try:
    # Try to override with the real app
    from app.main import app as real_app
    app = real_app
except Exception as e:
    # If the real app fails to load, this minimal app will catch it 
    # and we can visit /api/health-check to see the error
    @app.get("/api/health-check")
    async def health_check():
        import traceback
        return {
            "status": "fatal_crash_during_import", 
            "detail": str(e), 
            "traceback": traceback.format_exc(),
            "path": sys.path,
            "cwd": os.getcwd()
        }

# Ensure Vercel finds the 'app' even if the import fails
handler = app
