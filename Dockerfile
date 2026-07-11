FROM python:3.12-slim

WORKDIR /app

# System dependencies for psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
WORKDIR /app/labtelemetry

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
