from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.shared.exceptions import AppError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.SENTRY_DSN:
        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
    if settings.DATABASE_URL.startswith("sqlite"):
        from app.database import async_session_factory, create_tables
        from app.modules.auth.seed import seed_all

        await create_tables()
        async with async_session_factory() as session:
            await seed_all(session)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.modules.auth.router import limiter

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(AppError)
    async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.message, "field": exc.field},
        )

    from app.modules.allocations.router import router as allocation_router
    from app.modules.auth.role_router import router as role_router
    from app.modules.auth.router import router as auth_router
    from app.modules.auth.user_router import router as user_router
    from app.modules.clients.router import router as client_router
    from app.modules.financial.router import router as financial_router
    from app.modules.invoicing.router import router as invoicing_router
    from app.modules.nonhuman_costs.router import router as nonhuman_cost_router
    from app.modules.projects.router import router as project_router
    from app.modules.resources.router import router as resource_router
    from app.modules.utilization.router import router as utilization_router
    from app.modules.worklogs.router import router as worklog_router

    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(role_router)
    app.include_router(resource_router)
    app.include_router(client_router)
    app.include_router(project_router)
    app.include_router(allocation_router)
    app.include_router(utilization_router)
    app.include_router(worklog_router)
    app.include_router(nonhuman_cost_router)
    app.include_router(invoicing_router)
    app.include_router(financial_router)

    @app.get("/api/v1/health")
    async def health_check() -> dict:
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()
