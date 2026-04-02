import sys
import os
from fastapi import FastAPI

# Hardened Path Resolution
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(base_dir, "backend")

if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    # Try to import the real app
    from app.main import app
except ImportError as e:
    # Minimal fallback app for debugging
    app = FastAPI()
    @app.get("/api/health-check")
    async def health_check():
        return {"status": "import_error", "detail": str(e), "path": sys.path}

# Vercel expects a top-level object named 'app' or 'handler'
# We'll use 'app' as it's the standard for FastAPI
