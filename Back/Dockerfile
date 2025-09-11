FROM python:3.11-slim

WORKDIR /app

ARG BUILD_ID=latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p Data/logs PDF\ Loans

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# FIXED: Use the correct module path
ENV PYTHONPATH=/app
CMD python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2