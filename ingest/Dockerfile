# MCP Chat Log Intelligence System - Ingest CLI Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-c", "print('Ingestion CLI ready')"]