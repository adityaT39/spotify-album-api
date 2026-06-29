"""Custom lists — user-curated collections of albums and tracks."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ListItem, MediaList, User
from app.schemas import (
    ListCreate,
    ListDetailOut,
    ListItemCreate,
    ListItemOut,
    ListOut,
    ListUpdate,
)
from app.security import get_current_user
from app.services import spotify

router = APIRouter(prefix="/lists", tags=["lists"])


def _get_owned_list(list_id: int, user: User, db: Session) -> MediaList:
    """Fetch a list, 404ing if it doesn't exist or isn't this user's."""
    media_list = db.get(MediaList, list_id)
    if media_list is None or media_list.user_id != user.id:
        raise HTTPException(status_code=404, detail="List not found")
    return media_list


@router.post("", response_model=ListOut, status_code=status.HTTP_201_CREATED)
def create_list(
    payload: ListCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MediaList:
    media_list = MediaList(
        user_id=user.id, name=payload.name, description=payload.description
    )
    db.add(media_list)
    db.commit()
    db.refresh(media_list)
    return media_list


@router.get("", response_model=list[ListOut])
def list_lists(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MediaList]:
    return (
        db.query(MediaList)
        .filter(MediaList.user_id == user.id)
        .order_by(MediaList.created_at.desc())
        .all()
    )


@router.get("/{list_id}", response_model=ListDetailOut)
def get_list(
    list_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MediaList:
    return _get_owned_list(list_id, user, db)


@router.patch("/{list_id}", response_model=ListOut)
def update_list(
    list_id: int,
    payload: ListUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MediaList:
    media_list = _get_owned_list(list_id, user, db)
    if payload.name is not None:
        media_list.name = payload.name
    if payload.description is not None:
        media_list.description = payload.description
    db.commit()
    db.refresh(media_list)
    return media_list


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    list_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    media_list = _get_owned_list(list_id, user, db)
    db.delete(media_list)
    db.commit()


@router.post(
    "/{list_id}/items",
    response_model=ListItemOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_item(
    list_id: int,
    payload: ListItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListItem:
    _get_owned_list(list_id, user, db)  # ownership check

    existing = (
        db.query(ListItem)
        .filter(
            ListItem.list_id == list_id,
            ListItem.item_type == payload.item_type,
            ListItem.spotify_id == payload.spotify_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="That's already in this list."
        )

    token = await spotify.get_valid_access_token(user, db)
    item = await spotify.get_item(token, payload.item_type, payload.spotify_id)

    list_item = ListItem(
        list_id=list_id,
        item_type=payload.item_type,
        spotify_id=item["id"],
        title=item["name"],
        artist=item["artist"],
        spotify_url=item.get("spotify_url"),
    )
    db.add(list_item)
    db.commit()
    db.refresh(list_item)
    return list_item


@router.delete(
    "/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_item(
    list_id: int,
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    media_list = _get_owned_list(list_id, user, db)
    item = db.get(ListItem, item_id)
    if item is None or item.list_id != media_list.id:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
