# Phase 10: local synthetic NAWA dashboard. Not a production deployment.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/demo
COPY demo/requirements-pdf.txt /tmp/nawa-requirements.txt
COPY demo/requirements-phase13.txt /tmp/nawa-phase13-requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/nawa-requirements.txt \
    && python -m pip install --no-cache-dir -r /tmp/nawa-phase13-requirements.txt \
    && python -m pip install --no-cache-dir 'psycopg[binary]>=3.2,<4' 'PyJWT[crypto]>=2.10,<3' \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin nawa

COPY demo/ /app/demo/
USER 10001:10001
EXPOSE 8765

HEALTHCHECK --interval=20s --timeout=12s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/ready', timeout=10).close()" || exit 1

CMD ["python", "-m", "nawa_demo.dashboard_container"]
