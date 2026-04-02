import sys
import os
from fastapi import FastAPI

# Hardened Path Resolution
# This ensures that even if Vercel starts in a different directory, we find the backend
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(base_dir, "backend")

if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    from app.main import app
except ImportError as e:
    # Fallback app for debugging 500 errors in Vercel
    app = FastAPI()
    @app.get("/api/health-check")
    async def health_check():
        return {
            "status": "error", 
            "message": f"Could not import app.main. Error: {str(e)}",
            "sys_path": sys.path,
            "cwd": os.getcwd(),
            "base_dir": base_dir,
            "backend_dir": backend_dir
        }

# This is the object Vercel consumes
handler = app
