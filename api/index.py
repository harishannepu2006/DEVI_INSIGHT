import sys
import os

# Add the backend directory to the sys.path so we can import the app
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app

# This is the object Vercel will use to run the serverless function
# Export app as handler if needed, but Vercel handles ASGI/WSGI apps directly
handler = app
