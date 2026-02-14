from fastapi import FastAPI
from app.config import settings
from app.api.routes import router
from app.deps import build_orchestrator


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

    @app.on_event("startup")
    async def startup():
        app.state.orchestrator = build_orchestrator()

    app.include_router(router, prefix=settings.API_PREFIX)
    return app


app = create_app()
