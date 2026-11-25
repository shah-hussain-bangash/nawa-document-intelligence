# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend/src
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils tesseract-ocr tesseract-ocr-eng tesseract-ocr-ara \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.lock ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install --no-cache-dir --require-hashes -r requirements.lock
COPY backend ./backend
COPY data/ocr ./data/ocr
COPY migrations ./migrations
COPY alembic.ini ./
RUN groupadd --gid 10001 nawa && useradd --uid 10001 --gid 10001 --no-create-home nawa \
    && mkdir -p /app/.data/uploads && chown -R nawa:nawa /app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=4s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready')"
CMD ["python", "-m", "uvicorn", "uae_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]

