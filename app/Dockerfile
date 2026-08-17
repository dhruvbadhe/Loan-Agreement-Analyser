FROM python:3.9-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

COPY app/ ./app

# Expose the API port (Render overrides this, but good for local)
EXPOSE 8000

# Start uvicorn server binding to dynamic port environment variable
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]