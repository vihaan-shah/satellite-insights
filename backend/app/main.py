import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load .env from the repo root (satellite-insights/.env) or backend/.env —
# whichever exists first, so it works regardless of where uvicorn is launched.
_here = Path(__file__).resolve()
for _candidate in [
    _here.parents[2] / ".env",   # satellite-insights/.env  (repo root)
    _here.parents[1] / ".env",   # satellite-insights/backend/.env
]:
    if _candidate.exists():
        load_dotenv(_candidate, override=False)
        print(f"[env] Loaded {_candidate}")
        break

from app.api.routes import router
from app.store.db import init_db
from app.store.vectorstore import init_vectorstore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and vector store on startup."""
    init_db()
    init_vectorstore()
    yield


app = FastAPI(
    title="Satellite-to-Insights API",
    description="Turns live satellite data into plain-English mission-ready briefs via IBM Granite.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
