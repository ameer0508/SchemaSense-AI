"""Aggregated API router for SchemaSense AI."""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.capabilities import router as capabilities_router
from app.api.v1.databases import router as databases_router
from app.api.v1.ai import router as ai_router
from app.api.v1.sql import router as sql_router
from app.api.v1.history import router as history_router
from app.api.v1.analytics import router as analytics_router

api_router = APIRouter()

# Mount endpoints directly under /api
api_router.include_router(health_router)
api_router.include_router(capabilities_router)
api_router.include_router(databases_router)
api_router.include_router(ai_router)
api_router.include_router(sql_router)
api_router.include_router(history_router)
api_router.include_router(analytics_router)

# Also expose under /v1 for versioned API routing
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router)
v1_router.include_router(capabilities_router)
v1_router.include_router(databases_router)
v1_router.include_router(ai_router)
v1_router.include_router(sql_router)
v1_router.include_router(history_router)
v1_router.include_router(analytics_router)
api_router.include_router(v1_router)

