"""SQLAlchemy ORM models — the shape of our database tables.

Ratings and listen-list entries are "media items": each one is either a whole
album or a single track, distinguished by `item_type`. Modeling it this way lets
the same tables and endpoints handle both.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """A person who has logged in with Spotify."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    spotify_user_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(255))

    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    ratings: Mapped[list["Rating"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    listen_list: Mapped[list["ListenListItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    lists: Mapped[list["MediaList"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Rating(Base):
    """A user's rating of a music item — an album or a single track."""

    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    item_type: Mapped[str] = mapped_column(String(16))  # "album" or "track"
    spotify_id: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(512))
    artist: Mapped[str] = mapped_column(String(512))
    spotify_url: Mapped[str | None] = mapped_column(Text)

    rating: Mapped[int] = mapped_column(Integer)  # 1-10
    review: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="ratings")


class ListenListItem(Base):
    """An album or track the user wants to listen to later."""

    __tablename__ = "listen_list"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    item_type: Mapped[str] = mapped_column(String(16))  # "album" or "track"
    spotify_id: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(512))
    artist: Mapped[str] = mapped_column(String(512))
    spotify_url: Mapped[str | None] = mapped_column(Text)

    added_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="listen_list")


class MediaList(Base):
    """A user-curated list of albums and/or tracks (e.g. "Best of 2024")."""

    __tablename__ = "lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="lists")
    items: Mapped[list["ListItem"]] = relationship(
        back_populates="media_list",
        cascade="all, delete-orphan",
        order_by="ListItem.added_at",
    )


class ListItem(Base):
    """An album or track inside a user's custom list."""

    __tablename__ = "list_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("lists.id"), index=True)

    item_type: Mapped[str] = mapped_column(String(16))  # "album" or "track"
    spotify_id: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(512))
    artist: Mapped[str] = mapped_column(String(512))
    spotify_url: Mapped[str | None] = mapped_column(Text)

    added_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    media_list: Mapped["MediaList"] = relationship(back_populates="items")
