from fastapi import FastAPI
import sys
import os

app = FastAPI()

@app.get("/api/health-check")
async def isolation_health():
    """Ultimate isolation diagnostic."""
    try:
        # Reflect the directories to see where we are
        # Vercel's root directory is usually the parent of /api
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # Check for key directories
        has_backend = os.path.exists(os.path.join(project_root, "backend"))
        has_frontend = os.path.exists(os.path.join(project_root, "frontend"))
        
        # List what we can see for deep manual inspection
        root_ls = os.listdir(project_root) if os.path.exists(project_root) else ["PARENT NOT ACCESSIBLE"]
        api_ls = os.listdir(os.path.dirname(__file__)) if os.path.exists(os.path.dirname(__file__)) else ["CURRENT NOT ACCESSIBLE"]
        
        return {
            "status": "ISOLATED_READY",
            "message": "Python runtime is working. The entry point is isolated.",
            "cwd": os.getcwd(),
            "sys_path": sys.path,
            "project_root": project_root,
            "visibility": {
                "backend": has_backend,
                "frontend": has_frontend,
                "root_ls": root_ls,
                "api_ls": api_ls
            }
        }
    except Exception as e:
        return {
            "status": "ISOLATION_FAILURE",
            "error": str(e)
        }

# Ensure Vercel finds the handler
handler = app
