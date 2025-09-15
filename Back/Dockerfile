FROM python:3.11-slim

WORKDIR /app

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

# Create necessary directories (without spaces)
RUN mkdir -p Data/logs PDF Loans  

# Create symlink for backward compatibility
RUN ln -s /app/PDF Loans "/app/PDF Loans"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set Python path
ENV PYTHONPATH=/app

# Use a single CMD script
CMD ["sh", "-c", "\
echo '=== Starting Finn Backend ==='; \
\
for i in $(seq 1 10); do \
    echo \"Attempt $i: Checking if Ollama is ready...\"; \
    if curl -f http://ollama:11434 >/dev/null 2>&1; then \
        echo '✅ Ollama is ready'; \
        break; \
    else \
        echo \"⚠️ Ollama not ready yet, attempt $i/10\"; \
        if [ $i -eq 10 ]; then \
            echo '❌ Ollama not available after 10 attempts, continuing anyway...'; \
        fi; \
        sleep 5; \
    fi; \
done; \
\
for i in $(seq 1 5); do \
    echo \"Attempt $i: Running database migration...\"; \
    if python migrate_data.py 2>&1; then \
        echo '✅ Migration completed successfully'; \
        break; \
    else \
        echo \"⚠️ Migration failed, attempt $i/5\"; \
        if [ $i -eq 5 ]; then \
            echo '❌ All migration attempts failed, checking DB...'; \
            python - <<'PYCODE' || exit 1 \
import sqlite3; \
conn = sqlite3.connect('loan_analysis.db'); \
cursor = conn.cursor(); \
cursor.execute('SELECT count(*) FROM sqlite_master WHERE type=\"table\"'); \
table_count = cursor.fetchone()[0]; \
print(f'Table count: {table_count}'); \
conn.close(); \
exit(0 if table_count > 0 else 1) \
PYCODE \
            echo '✅ Database has tables, continuing...'; \
            break; \
        fi; \
        sleep 5; \
    fi; \
done; \
\
echo 'Starting FastAPI server...'; \
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 \
"]
