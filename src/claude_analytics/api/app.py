from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from claude_analytics.api.v1 import router as analytics_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Claude Code Analytics API",
        version="0.1.0",
        description="API layer for telemetry analytics over Claude Code usage data.",
    )

    @app.get("/health", tags=["system"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(ValueError)
    async def handle_value_error(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Database error while processing request.", "error": str(exc.__class__.__name__)},
        )

    app.include_router(analytics_router, prefix="/api/v1")
    return app


app = create_app()
