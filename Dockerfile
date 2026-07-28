FROM python:3.12-slim

WORKDIR /app

# System dependencies for psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# O bit de execucao do entrypoint esta registrado no git, mas nem todo caminho
# ate aqui o preserva (download em zip, checkout no Windows, `COPY` a partir de
# um contexto reconstruido). Sem isto o container morre no boot com
# "permission denied" antes de rodar uma linha sequer.
RUN chmod +x /app/docker-entrypoint.sh

WORKDIR /app/labtelemetry

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
