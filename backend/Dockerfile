# Use official lightweight Python image
FROM python:3.11-slim

# Set environment paths
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

# Install system dependencies needed for compiling psycopg2 and general helper utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ./app /workspace/app

# Expose API Gateway Port
EXPOSE 8000

# Run FastAPI gateway
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
