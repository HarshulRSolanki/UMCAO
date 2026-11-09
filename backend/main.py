"""FastAPI application entry point for UMCAO (Universal Multi-Language Code Analyzer and Optimizer)."""

import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Ensure backend directory is on sys.path whether invoked from root or backend/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from api.routes import router as api_router, health_check  # noqa: E402
from api.ai_routes import router as ai_router  # noqa: E402
from api.code_routes import router as code_router  # noqa: E402

# Load environment configuration (if .env exists locally)
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

app = FastAPI(
    title="UMCAO API",
    description="Universal Multi-Language Code Analyzer and Optimizer - Backend Engine",
    version="1.0.0",
)

# Parse CORS allowed origins from environment variable + sensible defaults
default_origins = [
    "https://umcao.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
cors_env = os.getenv("CORS_ORIGINS", "")
env_origins = [o.strip().rstrip("/") for o in cors_env.split(",") if o.strip() and o.strip() != "*"]
allowed_origins = list(dict.fromkeys(default_origins + env_origins))

# Enable CORS middleware (supports explicit origins + all *.onrender.com subdomains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ai_router)
app.include_router(code_router)


@app.get("/health")
def root_health_check():
    """Health endpoint alias for cloud load balancers and Render health checks."""
    return health_check()


# Optional: Serve built React SPA when deployed as a unified single-container service
SERVE_FRONTEND = os.getenv("SERVE_FRONTEND", "").lower() in ("1", "true", "yes")
DIST_CANDIDATES = [
    os.path.join(BASE_DIR, "static"),
    os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "dist")),
]
FRONTEND_DIST = next((p for p in DIST_CANDIDATES if os.path.isfile(os.path.join(p, "index.html"))), None)

if SERVE_FRONTEND and FRONTEND_DIST:
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json", "health"):
            raise HTTPException(status_code=404, detail="Endpoint not found")
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "app": "UMCAO (Universal Multi-Language Code Analyzer and Optimizer)",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
            "languages": "/api/languages",
            "features": [
                "Static AST Analysis & Complexity Estimation",
                "Compilation Error Detection & Output Execution",
                "Gemini AI Code & Error Explanations (English, Gujarati, Hindi)",
            ],
        }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    is_prod = bool(os.getenv("RENDER") or os.getenv("PORT"))
    uvicorn.run("main:app", host=host, port=port, reload=not is_prod)
