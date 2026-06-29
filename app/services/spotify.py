"""Thin client for Spotify's OAuth endpoints and Web API.

Note: Spotify restricts *write* access (saving to a library, modifying
playlists) to apps with Extended Quota, which isn't available to hobby/dev-mode
apps. So this client uses Spotify read-only — login, catalog search, and reading
the user's existing library. The app itself is the system of record for ratings
and lists.
"""

import base64
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

# Read-only permissions: the user's email and their saved albums.
SCOPES = "user-read-email user-library-read"


def build_authorize_url(state: str) -> str:
    """Build the Spotify consent URL we redirect the user to (step 2 of OAuth)."""
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": SCOPES,
        "state": state,
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"


def _basic_auth_header() -> dict[str, str]:
    """Spotify's token endpoint authenticates the app with HTTP Basic auth."""
    raw = f"{settings.spotify_client_id}:{settings.spotify_client_secret}"
    encoded = base64.b64encode(raw.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


async def exchange_code_for_tokens(code: str) -> dict:
    """Trade the one-time authorization code for access + refresh tokens."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
            },
            headers=_basic_auth_header(),
        )
    resp.raise_for_status()
    return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Get a fresh access token using a stored refresh token."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            SPOTIFY_TOKEN_URL,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            headers=_basic_auth_header(),
        )
    resp.raise_for_status()
    return resp.json()


async def get_valid_access_token(user: User, db: Session) -> str:
    """Return a usable Spotify access token for this user, refreshing it first
    if it has expired (or is about to). Access tokens last ~1 hour."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    not_expiring_soon = (
        user.token_expires_at is not None
        and user.token_expires_at > now + timedelta(seconds=60)
    )
    if not_expiring_soon:
        return user.access_token

    if not user.refresh_token:
        return user.access_token  # nothing to refresh with; use what we have

    new = await refresh_access_token(user.refresh_token)
    user.access_token = new["access_token"]
    if new.get("refresh_token"):
        user.refresh_token = new["refresh_token"]
    user.token_expires_at = now + timedelta(seconds=new.get("expires_in", 3600))
    db.commit()
    db.refresh(user)
    return user.access_token


def _artists(obj: dict) -> str:
    return ", ".join(a["name"] for a in obj.get("artists", []))


def _simplify_album(album: dict) -> dict:
    """Trim Spotify's album object down to the fields we care about."""
    images = album.get("images") or []
    return {
        "id": album["id"],
        "name": album["name"],
        "artist": _artists(album),
        "release_date": album.get("release_date"),
        "image_url": images[0]["url"] if images else None,
        "spotify_url": (album.get("external_urls") or {}).get("spotify"),
        "total_tracks": album.get("total_tracks"),
    }


def _simplify_track(track: dict) -> dict:
    """Trim Spotify's track object down to the fields we care about."""
    album = track.get("album") or {}
    images = album.get("images") or []
    return {
        "id": track["id"],
        "name": track["name"],
        "artist": _artists(track),
        "album": album.get("name"),
        "image_url": images[0]["url"] if images else None,
        "spotify_url": (track.get("external_urls") or {}).get("spotify"),
        "duration_ms": track.get("duration_ms"),
    }


async def _get(access_token: str, path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{SPOTIFY_API_BASE}{path}",
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


async def get_current_user_profile(access_token: str) -> dict:
    """Fetch the logged-in Spotify user's profile (id, display name, email)."""
    return await _get(access_token, "/me")


async def search_albums(
    access_token: str, query: str, limit: int = 10
) -> list[dict]:
    """Search the Spotify catalog for albums matching `query`."""
    data = await _get(
        access_token, "/search", {"q": query, "type": "album", "limit": limit}
    )
    items = data.get("albums", {}).get("items", [])
    return [_simplify_album(item) for item in items]


async def search_tracks(
    access_token: str, query: str, limit: int = 10
) -> list[dict]:
    """Search the Spotify catalog for tracks (songs) matching `query`."""
    data = await _get(
        access_token, "/search", {"q": query, "type": "track", "limit": limit}
    )
    items = data.get("tracks", {}).get("items", [])
    return [_simplify_track(item) for item in items]


async def get_album(access_token: str, album_id: str) -> dict:
    """Look up a single album by its Spotify id."""
    return _simplify_album(await _get(access_token, f"/albums/{album_id}"))


async def get_track(access_token: str, track_id: str) -> dict:
    """Look up a single track by its Spotify id."""
    return _simplify_track(await _get(access_token, f"/tracks/{track_id}"))


async def get_item(access_token: str, item_type: str, spotify_id: str) -> dict:
    """Look up either an album or a track, returning a normalized dict with
    id / name / artist / spotify_url."""
    if item_type == "track":
        return await get_track(access_token, spotify_id)
    return await get_album(access_token, spotify_id)


async def get_saved_albums(access_token: str, limit: int = 20) -> list[dict]:
    """List albums saved in the user's Spotify library (read-only)."""
    data = await _get(access_token, "/me/albums", {"limit": limit})
    items = data.get("items", [])
    return [
        _simplify_album(item["album"]) for item in items if item.get("album")
    ]
