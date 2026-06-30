FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY studob/ studob/
COPY data/concept_graph.json data/
COPY configs/ configs/
COPY scripts/ scripts/

RUN pip install --no-cache-dir -e . && \
    mkdir -p /app/data

EXPOSE 8000

COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
