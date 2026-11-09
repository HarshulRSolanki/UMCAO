# ==============================================================================
# UMCAO - Unified Multi-Stage Dockerfile (Frontend + Backend + 5 Runtimes)
# Supports Python, JavaScript (Node.js), C (GCC), C++ (G++), and Java (JDK)
# ==============================================================================

# Stage 1: Build React + Vite Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
ENV VITE_API_BASE_URL=/api
RUN npm run build

# Stage 2: FastAPI Backend + Language Compilers/Runtimes
FROM python:3.12-slim
WORKDIR /app

# Install system compilers/runtimes for multi-language execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-jdk-headless \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source and built frontend static bundle
COPY backend/ ./
COPY --from=frontend-builder /frontend/dist ./static

ENV PYTHONUNBUFFERED=1
ENV SERVE_FRONTEND=true
ENV PORT=10000

EXPOSE 10000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]

