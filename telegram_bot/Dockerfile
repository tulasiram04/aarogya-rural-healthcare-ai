# Use official lightweight Python image
FROM python:3.11-slim

# Set environment paths
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements.txt as they share imports
COPY ./backend/requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source trees
COPY ./backend /workspace/backend
COPY ./telegram_bot /workspace/telegram_bot

WORKDIR /workspace/telegram_bot

# Launch the bot polling app
CMD ["python", "bot/main.py"]
