"""Track (song) search and lookup, backed by the Spotify catalog (Redis-cached)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import TrackOut
from app.security import get_current_user
from app.services import cache, spotify

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("/search", response_model=list[TrackOut])
async def search_tracks(
    q: str = Query(..., min_length=1, description="What to search for"),
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    key = f"tracks:search:{q.lower()}:{limit}"
    cached = cache.get_json(key)
    if cached is not None:
        return cached
    token = await spotify.get_valid_access_token(user, db)
    results = await spotify.search_tracks(token, q, limit)
    cache.set_json(key, results, ttl=3600)
    return results


@router.get("/{track_id}", response_model=TrackOut)
async def get_track(
    track_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    key = f"track:{track_id}"
    cached = cache.get_json(key)
    if cached is not None:
        return cached
    token = await spotify.get_valid_access_token(user, db)
    track = await spotify.get_track(token, track_id)
    cache.set_json(key, track, ttl=86400)
    return track
