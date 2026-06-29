"""Shared test fixtures.

Tests run against a throwaway in-memory SQLite database and mock out all calls
to Spotify, so the suite is fast, deterministic, and needs no network or real
credentials.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.security import create_access_token
from app.services import spotify


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def user(db_session) -> User:
    u = User(
        spotify_user_id="test-user",
        display_name="Tester",
        access_token="access",
        refresh_token="refresh",
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


@pytest.fixture(autouse=True)
def mock_spotify(monkeypatch):
    """Replace the Spotify client with fast, offline fakes."""

    async def fake_token(user, db):
        return "fake-token"

    async def fake_get_item(token, item_type, spotify_id):
        return {
            "id": spotify_id,
            "name": f"Test {item_type} {spotify_id}",
            "artist": "Test Artist",
            "spotify_url": f"https://open.spotify.com/{item_type}/{spotify_id}",
        }

    async def fake_search_albums(token, query, limit=10):
        return [
            {
                "id": "album123",
                "name": f"{query} (album)",
                "artist": "Test Artist",
                "release_date": "2020-01-01",
                "image_url": None,
                "spotify_url": "https://open.spotify.com/album/album123",
                "total_tracks": 10,
            }
        ]

    async def fake_search_tracks(token, query, limit=10):
        return [
            {
                "id": "track123",
                "name": f"{query} (song)",
                "artist": "Test Artist",
                "album": "Test Album",
                "image_url": None,
                "spotify_url": "https://open.spotify.com/track/track123",
                "duration_ms": 200000,
            }
        ]

    monkeypatch.setattr(spotify, "get_valid_access_token", fake_token)
    monkeypatch.setattr(spotify, "get_item", fake_get_item)
    monkeypatch.setattr(spotify, "search_albums", fake_search_albums)
    monkeypatch.setattr(spotify, "search_tracks", fake_search_tracks)
