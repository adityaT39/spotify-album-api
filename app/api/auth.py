"""Spotify OAuth login and callback routes."""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import create_access_token
from app.services import spotify

router = APIRouter(prefix="/auth/spotify", tags=["auth"])

STATE_COOKIE = "spotify_oauth_state"


@router.get("/login")
def login() -> RedirectResponse:
    """Step 1-2: send the user to Spotify to log in and grant access.

    We generate a random `state` and stash it in a short-lived cookie so we can
    verify, on the way back, that the callback was triggered by *our* request
    (CSRF protection).
    """
    state = secrets.token_urlsafe(16)
    response = RedirectResponse(spotify.build_authorize_url(state))
    response.set_cookie(
        STATE_COOKIE, state, httponly=True, max_age=600, samesite="lax"
    )
    return response


@router.get("/callback")
async def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Step 4-6: Spotify redirects back here with a code. We verify state,
    exchange the code for tokens, store the user, and issue our own JWT."""
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    if not state or state != request.cookies.get(STATE_COOKIE):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    tokens = await spotify.exchange_code_for_tokens(code)
    profile = await spotify.get_current_user_profile(tokens["access_token"])

    # Store naive UTC so it maps cleanly to the DB timestamp column.
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(seconds=tokens.get("expires_in", 3600))
    ).replace(tzinfo=None)

    # Upsert: create the user on first login, otherwise refresh their tokens.
    user = (
        db.query(User).filter(User.spotify_user_id == profile["id"]).first()
    )
    if user is None:
        user = User(spotify_user_id=profile["id"])
        db.add(user)
    user.display_name = profile.get("display_name")
    user.access_token = tokens["access_token"]
    user.refresh_token = tokens.get("refresh_token", user.refresh_token)
    user.token_expires_at = expires_at
    db.commit()
    db.refresh(user)

    app_token = create_access_token(user.id)
    response = JSONResponse(
        {
            "message": f"Logged in as {user.display_name or user.spotify_user_id}",
            "access_token": app_token,
            "token_type": "bearer",
        }
    )
    response.delete_cookie(STATE_COOKIE)
    return response
