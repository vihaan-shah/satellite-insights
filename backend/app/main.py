from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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
