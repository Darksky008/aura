import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin, assistant, public, voice
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging, log_ctx
from app.database.session import SessionLocal, engine, init_db

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    if settings.auto_create_tables:
        init_db()
    if settings.auto_seed:
        try:
            from seed.run import seed_demo

            with SessionLocal() as db:
                if seed_demo(db):
                    log.info("demo hotel seeded on startup")
        except Exception:  # noqa: BLE001
            log.exception("auto-seed failed")
    log.info("AURA backend ready", extra=log_ctx(env=settings.app_env, llm="groq" if settings.groq_api_key else "offline"))
    yield
    engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AURA Hotel Dining Concierge API", version="1.0.0", lifespan=lifespan,
                  description="Tool-driven AI concierge: menu, recommendations, voice, admin. Interactive docs at /docs.")
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_origin_regex=settings.cors_origin_regex or None,
                       allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Voice-Language"])

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        started = time.perf_counter()
        rid = uuid.uuid4().hex[:10]
        try:
            response = await call_next(request)
        except Exception:  # noqa: BLE001
            log.exception("unhandled", extra=log_ctx(endpoint=request.url.path, request_id=rid))
            return JSONResponse({"error": "Something went wrong. Please try again."}, status_code=500)
        response.headers["X-Request-ID"] = rid
        if request.url.path != "/api/health":
            log.info("request", extra=log_ctx(endpoint=request.url.path, method=request.method, status=response.status_code,
                                             latency_ms=int((time.perf_counter() - started) * 1000), request_id=rid))
        return response

    @app.exception_handler(AppError)
    async def app_error(_: Request, exc: AppError):
        return JSONResponse({"error": exc.public_message}, status_code=exc.status_code)

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException):
        return JSONResponse({"error": exc.detail}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        fields = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse({"error": "Please check the highlighted fields.", "fields": fields}, status_code=422)

    for router in (public.router, assistant.router, voice.router, admin.router):
        app.include_router(router, prefix="/api")

    @app.get("/", include_in_schema=False)
    def root():
        return {"name": "AURA Hotel Dining Concierge API", "docs": "/docs", "health": "/api/health"}

    return app


app = create_app()
