# ==============================================================================
# UMCAO Backend API Dockerfile (With Python, Node.js, GCC, G++, and JDK)
# For Render Web Service when Root Directory is set to 'backend'
# ==============================================================================

FROM python:3.12-slim
WORKDIR /app

# Install system compilers/runtimes for multi-language execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-jdk-headless \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

ENV PYTHONUNBUFFERED=1
ENV PORT=10000

EXPOSE 10000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]

