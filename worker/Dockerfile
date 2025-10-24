# EchoGarden Worker Dockerfile
FROM python:3.11-slim

# Ensure Python behaves consistently in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies required by Celery and database drivers, then clean up
RUN apt-get update \
 && apt-get install --no-install-recommends -y build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies before copying the source to leverage Docker layer caching
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the worker source code
COPY . .

# Launch the Celery worker
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
