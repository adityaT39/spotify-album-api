"""Pydantic schemas — the request/response shapes for the API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ItemType = Literal["album", "track"]


class AlbumOut(BaseModel):
    """A simplified album from the Spotify catalog."""

    id: str
    name: str
    artist: str
    release_date: str | None = None
    image_url: str | None = None
    spotify_url: str | None = None
    total_tracks: int | None = None


class TrackOut(BaseModel):
    """A simplified track (song) from the Spotify catalog."""

    id: str
    name: str
    artist: str
    album: str | None = None
    image_url: str | None = None
    spotify_url: str | None = None
    duration_ms: int | None = None


class RatingCreate(BaseModel):
    item_type: ItemType = "album"
    spotify_id: str
    rating: int = Field(ge=1, le=10, description="Your score, 1 to 10")
    review: str | None = None


class RatingUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=10)
    review: str | None = None


class RatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_type: ItemType
    spotify_id: str
    title: str
    artist: str
    spotify_url: str | None
    rating: int
    review: str | None
    created_at: datetime


class ListenListCreate(BaseModel):
    item_type: ItemType = "album"
    spotify_id: str


class ListenListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_type: ItemType
    spotify_id: str
    title: str
    artist: str
    spotify_url: str | None
    added_at: datetime


class ListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ListUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ListItemCreate(BaseModel):
    item_type: ItemType = "album"
    spotify_id: str


class ListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_type: ItemType
    spotify_id: str
    title: str
    artist: str
    spotify_url: str | None
    added_at: datetime


class ListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime


class ListDetailOut(ListOut):
    items: list[ListItemOut]
