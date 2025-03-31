from fastapi import FastAPI
from server.config import Settings
from server.routes import api_router, main_router, kb_router

def create_app(settings: Settings = None) -> FastAPI:
    if settings is None:
        from server.config import get_settings
        settings = get_settings()
    
    app = FastAPI(
        title="Astra Knowledge Base API",
        description="API for Astra Knowledge Base",
        version="0.1.0",
    )
    
    # Include routers
    app.include_router(main_router)
    app.include_router(api_router, prefix="/api")
    app.include_router(kb_router, prefix="/api")
    
    return app 