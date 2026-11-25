import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from uae_ai import __version__
from uae_ai.api import auth, workspace, history
from uae_ai.core.config import Settings
from uae_ai.core.migrations import migrate_local
from uae_ai.db import Base, make_database
from uae_ai.seed import seed
from uae_ai.domain.versions import bootstrap_versions


def create_app(settings=None):
    settings = settings or Settings()
    settings.validate()
    engine, factory = make_database(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        if settings.app_env in {"local", "test"}:
            migrate_local(engine, settings.database_url)
        if settings.seed_demo:
            with factory() as db:
                seed(db, settings)
        with factory() as db:
            bootstrap_versions(db)
        yield
        engine.dispose()

    app = FastAPI(title="Nawa Workspace API", version=__version__, lifespan=lifespan, docs_url="/api/docs" if settings.app_env != "production" else None, redoc_url=None)
    app.state.settings, app.state.engine, app.state.session_factory = settings, engine, factory
    requests = defaultdict(deque)

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        request.state.correlation_id = str(uuid4())
        ip = request.client.host if request.client else "unknown"
        key = (ip, "login" if request.url.path == "/auth/demo" else "api")
        timestamps = requests[key]
        current = time.monotonic()
        while timestamps and timestamps[0] < current - 60:
            timestamps.popleft()
        limit = 30 if key[1] == "login" else 500
        if len(timestamps) >= limit:
            return JSONResponse({"error": {"code": "RATE_LIMIT", "message": "Too many requests. Please wait a minute.", "correlation_id": request.state.correlation_id}}, status_code=429, headers={"Retry-After": "60"})
        timestamps.append(current)
        if len(requests) > 10000:
            for old in list(requests):
                if not requests[old] or requests[old][-1] < current - 60:
                    requests.pop(old, None)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            origins = {settings.web_origin}
            if settings.app_env in {"local", "test"} and settings.web_origin.startswith(("http://localhost:", "http://127.0.0.1:")):
                origins.add(settings.web_origin.replace("localhost", "127.0.0.1"))
                origins.add(settings.web_origin.replace("127.0.0.1", "localhost"))
            if origin and origin not in origins:
                return JSONResponse({"error": {"code": "ORIGIN", "message": "Origin not permitted."}}, status_code=403)
            length = request.headers.get("content-length", "0")
            if not length.isdigit() or int(length) > 11 * 1024 * 1024:
                return JSONResponse({"error": {"code": "SIZE", "message": "Request is too large."}}, status_code=413)
        response = await call_next(request)
        response.headers.update({"X-Request-ID": request.state.correlation_id, "X-Content-Type-Options": "nosniff", "Referrer-Policy": "same-origin", "X-Frame-Options": "DENY", "Cache-Control": "no-store"})
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        return JSONResponse({"error": {"code": f"HTTP_{exc.status_code}", "message": str(exc.detail), "correlation_id": getattr(request.state, "correlation_id", "")}}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        errors = [{"field": ".".join(str(x) for x in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse({"error": {"code": "VALIDATION", "message": "Check the supplied fields and try again.", "fields": errors, "correlation_id": getattr(request.state, "correlation_id", "")}}, status_code=422)

    @app.exception_handler(Exception)
    async def safe_error(request, exc):
        logging.getLogger("nawa").error("Request failed: %s (%s)", type(exc).__name__, getattr(request.state, "correlation_id", ""))
        return JSONResponse({"error": {"code": "INTERNAL", "message": "The request could not be completed safely.", "correlation_id": getattr(request.state, "correlation_id", "")}}, status_code=500)

    @app.get("/health/live")
    def live():
        return {"status": "ok", "version": __version__}

    @app.get("/health/ready")
    def ready():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                connection.execute(text("SELECT id FROM tenants LIMIT 1"))
            return {"status": "ready"}
        except Exception:
            raise HTTPException(503, "Database is unavailable.") from None

    app.include_router(auth.router)
    app.include_router(workspace.router)
    app.include_router(history.router)
    return app


app = create_app()
