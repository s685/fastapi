# Multi-stage Dockerfile optimized for Snowpark Container Services (SPCS)
# Uses Poetry for dependency management

# Stage 1: Builder - Install dependencies
FROM python:3.11-slim as builder

WORKDIR /build

# Install system dependencies including Poetry
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure Poetry to not create virtual env (we're in a container)
RUN poetry config virtualenvs.create false

# Install dependencies to system Python
RUN poetry install --no-root --no-dev --no-interaction --no-ansi


# Stage 2: Runtime - Create production image
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app /app/app

# Create non-root user for security (required by SPCS)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port for SPCS (must be 8080)
EXPOSE 8080

# Health check for SPCS
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()" || exit 1

# Run application with single worker (SPCS scales horizontally)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--log-level", "info"]
