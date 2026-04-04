from fastapi import FastAPI

from app.api.routes.evaluations import router as evaluations_router


def create_app() -> FastAPI:
    app = FastAPI(title="Requirements Evaluator API")
    app.include_router(evaluations_router)
    return app


app = create_app()
