from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from app.api.v1 import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settingsNone.API_V1_STR}/openapi.json",
        docs_url=,
        redoc_url=None,
    )

    # Set up CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Custom API docs
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=f"{settings.API_V1_STR}/openapi.json",
            title=f"{settings.PROJECT_NAME} - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=f"{settings.API_V1_STR}/openapi.json",
            title=f"{settings.PROJECT_NAME} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        )

    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "Welcome to the Secure Document Management API. Visit /docs for the API documentation."}

    return app
