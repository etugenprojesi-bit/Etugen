"""FastAPI application. Run: backend/.venv/Scripts/python -m uvicorn app.main:app --app-dir backend"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import logging_privacy
from app.api.analyze import router as analyze_router
from app.api.rotations import router as rotations_router
from app.api.risk import router as risk_router
from app.api.satellite import router as satellite_router

logging_privacy.install()  # no coordinates next to IP addresses in access logs
app = FastAPI(title="Etügen API", version="0.1.0")
app.add_middleware(  # the PWA dev server runs on another port
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"],
)
app.include_router(analyze_router)
app.include_router(rotations_router)
app.include_router(satellite_router)
app.include_router(risk_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# Deployment (deploy/huggingface/): the built PWA (`npm run build` -> frontend/dist) is served
# from the same address as the API. In development Vite serves it instead and this is skipped.
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if (_DIST / "index.html").exists():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="pwa")
