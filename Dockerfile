# Stage 1: Build the Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Backend & Unified Static Hosting
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./app

# Copy built frontend from Stage 1 to the backend's static directory
COPY --from=frontend-builder /app/frontend/dist ./static

# Set Environment Variables
ENV PYTHONPATH=/app
ENV APP_ENV=production
ENV PORT=8000

# Expose the API port
EXPOSE 8000

# Default command (can be overridden by Railway for the worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
