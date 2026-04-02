import sys
import os

# Add backend to path so we can import 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

# Vercel needs this top-level assignment
from app.main import app as handler

# Also keep 'app' just in case
app = handler
