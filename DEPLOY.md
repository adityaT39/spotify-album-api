# Deploying to Render

The app deploys as three services defined in [`render.yaml`](render.yaml):
a Dockerized FastAPI web service, a managed **PostgreSQL** database, and a
**Redis (Key Value)** cache. `DATABASE_URL`, `REDIS_URL`, and `JWT_SECRET` are
wired automatically; you only supply the Spotify credentials.

## Steps

1. Make sure your code is pushed to GitHub (it is).
2. In the [Render Dashboard](https://dashboard.render.com): **New → Blueprint**,
   then select this repository. Render reads `render.yaml` and sets up all three
   services.
3. Render prompts for the `sync: false` values:
   - `SPOTIFY_CLIENT_ID` — from your Spotify app
   - `SPOTIFY_CLIENT_SECRET` — from your Spotify app
   - `SPOTIFY_REDIRECT_URI` — leave blank for now (set in step 5)
4. Apply the blueprint and wait for the web service to build and go live. Note
   its URL, e.g. `https://spotify-album-api.onrender.com`.
5. Set the redirect URI in **two** places — they must match **exactly**:
   - **Render**: set the web service env var
     `SPOTIFY_REDIRECT_URI = https://YOUR-APP.onrender.com/auth/spotify/callback`
     (saving this triggers a redeploy).
   - **Spotify Developer Dashboard** → your app → **Settings → Redirect URIs**:
     add the same URL.
6. Open `https://YOUR-APP.onrender.com/docs` and log in at
   `https://YOUR-APP.onrender.com/auth/spotify/login`.

## Notes

- Free web services **sleep when idle** — the first request after a pause is slow.
- The free PostgreSQL instance **expires ~90 days** after creation.
- Database migrations run automatically on each deploy (`alembic upgrade head`
  is part of the container start command).
- Your Spotify app is in **development mode**, so only the owner account (or
  users you add under Settings → User Management) can log in.
- If the DB connection fails on SSL, append `?sslmode=require` to `DATABASE_URL`.
