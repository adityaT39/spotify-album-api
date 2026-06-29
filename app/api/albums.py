"""Album search and lookup, backed by the Spotify catalog."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import AlbumOut
from app.security import get_current_user
from app.services import spotify

router = APIRouter(prefix="/albums", tags=["albums"])


@router.get("/search", response_model=list[AlbumOut])
async def search_albums(
    q: str = Query(..., min_length=1, description="What to search for"),
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    token = await spotify.get_valid_access_token(user, db)
    return await spotify.search_albums(token, q, limit)


@router.get("/{album_id}", response_model=AlbumOut)
async def get_album(
    album_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    token = await spotify.get_valid_access_token(user, db)
    return await spotify.get_album(token, album_id)
