"""
FastAPI application factory for DeTrace / Veridex (Step 9 / Step 11 UI).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
except ImportError:
    pass

from backend.api.routes import router as api_router

REACT_DIST_DIR = PROJECT_ROOT / "frontend-react" / "dist"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DeTrace — Enterprise Graph RAG API",
        description="Deterministic graph retrieval, dependency tracing, and grounded answer generation over HydraDB",
        version="0.11.0",
    )


    # CORS configuration for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes FIRST so they take precedence over catch-all SPA routes
    app.include_router(api_router)

    # Mount static assets & frontend
    if REACT_DIST_DIR.exists() and (REACT_DIST_DIR / "index.html").exists():
        assets_dir = REACT_DIST_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/", include_in_schema=False)
        def serve_react_root() -> FileResponse:
            return FileResponse(REACT_DIST_DIR / "index.html")

        @app.get("/{full_path:path}", include_in_schema=False)
        def serve_react_spa(full_path: str) -> FileResponse:
            target = REACT_DIST_DIR / full_path
            if target.exists() and target.is_file():
                return FileResponse(target)
            return FileResponse(REACT_DIST_DIR / "index.html")

    elif FRONTEND_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

        @app.get("/", include_in_schema=False)
        def serve_legacy_index() -> FileResponse:
            return FileResponse(FRONTEND_DIR / "index.html")

    return app


app = create_app()
