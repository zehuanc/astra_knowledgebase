from fastapi import APIRouter
from server.routes.main import router as main_router
from server.routes.api import router as api_router
from server.routes.knowledge_base import router as kb_router

__all__ = ["main_router", "api_router", "kb_router"] 