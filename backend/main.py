"""FastAPI application entry point for UMCAO (Universal Multi-Language Code Analyzer and Optimizer)."""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
from api.ai_routes import router as ai_router
from api.code_routes import router as code_router

# Load environment configuration
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path=ENV_PATH)

app = FastAPI(
    title="UMCAO API",
    description="Universal Multi-Language Code Analyzer and Optimizer - Backend Engine",
    version="1.0.0",
)

# Parse CORS allowed origins from environment variable
cors_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,*")
allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]

# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=
    ["https://umcao.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ai_router)
app.include_router(code_router)


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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
