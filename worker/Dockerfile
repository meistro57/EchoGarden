# MCP Chat Log Intelligence System - Worker Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY worker/requirements.txt .
RUN pip install -r requirements.txt

COPY worker/ .

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]