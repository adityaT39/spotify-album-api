"""Read the user's existing Spotify library.

Spotify only allows hobby/dev-mode apps read access here (writing to the library
requires Extended Quota), so this is view-only — handy for seeing or importing
the albums you've already saved on Spotify.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import AlbumOut
from app.security import get_current_user
from app.services import spotify

router = APIRouter(prefix="/library", tags=["spotify library"])


@router.get("/albums", response_model=list[AlbumOut])
async def list_saved_albums(
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List albums the user has saved in their Spotify library."""
    token = await spotify.get_valid_access_token(user, db)
    return await spotify.get_saved_albums(token, limit)
