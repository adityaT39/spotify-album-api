"""Application entry point. Creates the FastAPI app and wires up routes."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import HTTPStatusError

from app import models  # noqa: F401  (import registers the models with Base)
from app.api import albums, auth, library, listen_list, lists, ratings, tracks
from app.config import settings
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup, create any tables that don't exist yet. For a portfolio
    # project this is fine; we'll switch to Alembic migrations later.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(albums.router)
app.include_router(tracks.router)
app.include_router(ratings.router)
app.include_router(listen_list.router)
app.include_router(lists.router)
app.include_router(library.router)


@app.exception_handler(HTTPStatusError)
async def spotify_error_handler(
    request: Request, exc: HTTPStatusError
) -> JSONResponse:
    """Translate errors from the Spotify API into clean HTTP responses."""
    code = exc.response.status_code
    status_code = code if 400 <= code < 500 else 502
    return JSONResponse(
        status_code=status_code,
        content={"detail": f"Spotify API error ({code})"},
    )


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Simple liveness check — handy for uptime monitoring and deploys."""
    return {"status": "ok", "app": settings.app_name}
