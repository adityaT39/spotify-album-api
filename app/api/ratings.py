"""Rate albums and tracks. Ratings are the app's own data."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Rating, User
from app.schemas import RatingCreate, RatingOut, RatingUpdate
from app.security import get_current_user
from app.services import spotify

router = APIRouter(prefix="/ratings", tags=["ratings"])


def _get_owned_rating(rating_id: int, user: User, db: Session) -> Rating:
    """Fetch a rating, 404ing if it doesn't exist or isn't this user's."""
    rating = db.get(Rating, rating_id)
    if rating is None or rating.user_id != user.id:
        raise HTTPException(status_code=404, detail="Rating not found")
    return rating


@router.post("", response_model=RatingOut, status_code=status.HTTP_201_CREATED)
async def create_rating(
    payload: RatingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Rating:
    existing = (
        db.query(Rating)
        .filter(
            Rating.user_id == user.id,
            Rating.item_type == payload.item_type,
            Rating.spotify_id == payload.spotify_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You already rated this — use PATCH to update it.",
        )

    # Pull the real title/artist from Spotify so our data is accurate.
    token = await spotify.get_valid_access_token(user, db)
    item = await spotify.get_item(token, payload.item_type, payload.spotify_id)

    rating = Rating(
        user_id=user.id,
        item_type=payload.item_type,
        spotify_id=item["id"],
        title=item["name"],
        artist=item["artist"],
        spotify_url=item.get("spotify_url"),
        rating=payload.rating,
        review=payload.review,
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


@router.get("", response_model=list[RatingOut])
def list_ratings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Rating]:
    return (
        db.query(Rating)
        .filter(Rating.user_id == user.id)
        .order_by(Rating.created_at.desc())
        .all()
    )


@router.patch("/{rating_id}", response_model=RatingOut)
def update_rating(
    rating_id: int,
    payload: RatingUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Rating:
    rating = _get_owned_rating(rating_id, user, db)
    if payload.rating is not None:
        rating.rating = payload.rating
    if payload.review is not None:
        rating.review = payload.review
    db.commit()
    db.refresh(rating)
    return rating


@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(
    rating_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    rating = _get_owned_rating(rating_id, user, db)
    db.delete(rating)
    db.commit()
