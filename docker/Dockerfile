# Multi-stage build for optimized production image
ARG PYTHON_VERSION=3.13

# Build stage
FROM python:${PYTHON_VERSION}-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY app/requirements.txt ./app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r app/requirements.txt

# Runtime stage
FROM python:${PYTHON_VERSION}-slim as runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser
