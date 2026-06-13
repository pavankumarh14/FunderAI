from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
from app.config.settings import settings

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

# Set more verbose logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

log = structlog.get_logger(__name__)

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(
        "🚀 GrantFlow starting",
        env=settings.app_env,
        llm_provider=settings.llm_provider,
        azure_endpoint=settings.azure_openai_endpoint or "(not configured)",
        deployment=settings.azure_openai_chat_deployment,
        static_dir_exists=STATIC_DIR.exists(),
        static_dir=str(STATIC_DIR),
        static_dir_contents=list(STATIC_DIR.iterdir()) if STATIC_DIR.exists() else [],
    )
    yield
    log.info("👋 GrantFlow shutting down")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    app = FastAPI(
        title="GrantFlow — Funding Opportunity Copilot",
        description=(
            "A LangGraph multi-agent system that helps researchers and startups "
            "find, evaluate, and prepare grant applications."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add exception handler to log all errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.exception(
            "🚨 Unhandled exception occurred",
            request_url=str(request.url),
            request_method=request.method,
            error=str(exc),
        )
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"}
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api")

    # Mount static files if directory exists
    if STATIC_DIR.exists():
        log.info("📂 Mounting static files directory", path=str(STATIC_DIR))
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    else:
        log.warning("⚠️ Static files directory not found", path=str(STATIC_DIR))

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
