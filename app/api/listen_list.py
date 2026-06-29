"""The user's listen list — albums or tracks they want to hear later."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ListenListItem, User
from app.schemas import ListenListCreate, ListenListOut
from app.security import get_current_user
from app.services import spotify

router = APIRouter(prefix="/listen-list", tags=["listen list"])


@router.post(
    "", response_model=ListenListOut, status_code=status.HTTP_201_CREATED
)
async def add_to_listen_list(
    payload: ListenListCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListenListItem:
    existing = (
        db.query(ListenListItem)
        .filter(
            ListenListItem.user_id == user.id,
            ListenListItem.item_type == payload.item_type,
            ListenListItem.spotify_id == payload.spotify_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="That's already on your listen list."
        )

    token = await spotify.get_valid_access_token(user, db)
    item = await spotify.get_item(token, payload.item_type, payload.spotify_id)

    entry = ListenListItem(
        user_id=user.id,
        item_type=payload.item_type,
        spotify_id=item["id"],
        title=item["name"],
        artist=item["artist"],
        spotify_url=item.get("spotify_url"),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("", response_model=list[ListenListOut])
def get_listen_list(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ListenListItem]:
    return (
        db.query(ListenListItem)
        .filter(ListenListItem.user_id == user.id)
        .order_by(ListenListItem.added_at.desc())
        .all()
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_listen_list(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    entry = db.get(ListenListItem, item_id)
    if entry is None or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(entry)
    db.commit()
