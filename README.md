# Album Rating API

[![CI](https://github.com/adityaT39/spotify-album-api/actions/workflows/ci.yml/badge.svg)](https://github.com/adityaT39/spotify-album-api/actions/workflows/ci.yml)

A backend REST API for rating music — think "Letterboxd, but for music." Users sign in
with **Spotify (OAuth 2.0)**, search albums and individual tracks, rate and review them,
and build listen lists and custom lists. The app is the **system of record** for your
ratings and lists; Spotify is used read-only (login, catalog search, and viewing your
existing library).

Built to demonstrate backend engineering: REST API design, OAuth 2.0, relational data,
automated testing, CI, and containerization.

## Tech stack

- **Python 3.12** + **FastAPI** (async REST API, auto-generated docs)
- **PostgreSQL** + **SQLAlchemy 2.0** ORM (falls back to SQLite for local runs)
- **Docker** + **docker-compose** (one command to run the whole stack)
- **Spotify Web API** via OAuth 2.0 Authorization Code flow *(in progress)*
- **httpx** for outbound API calls

## Getting started (with Docker — recommended)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) running.

```bash
# 1. Set up your environment file
cp .env.example .env

# 2. Build and run the whole stack (API + PostgreSQL)
docker compose up --build
```

Then open:

- http://127.0.0.1:8000/docs — interactive Swagger API docs
- http://127.0.0.1:8000/health — health check

Stop everything with `docker compose down`.

## Running without Docker (SQLite)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

This uses a local SQLite file instead of PostgreSQL — handy for quick local work.

## Deploy

Deployable to [Render](https://render.com) via the included
[`render.yaml`](render.yaml) blueprint (web service + PostgreSQL + Redis).
See [DEPLOY.md](DEPLOY.md) for the step-by-step guide.

## Project status

- [x] Project foundation: config, database, models, health check
- [x] Docker + PostgreSQL (`docker compose up`)
- [x] Spotify OAuth login (Authorization Code flow + token refresh)
- [x] Album **and track** search & lookup (Spotify catalog)
- [x] Rate albums and tracks (create / list / update / delete)
- [x] Listen list — save albums or tracks to hear later (with a Spotify play link)
- [x] View your existing Spotify library (read-only)
- [x] Custom lists (albums + tracks, e.g. "Best of 2024")
- [ ] Tests (pytest) + CI (GitHub Actions)
- [ ] Redis caching for catalog lookups

> **Design note:** Spotify restricts *write* access (saving to your library,
> modifying playlists) to apps with Extended Quota, which isn't available to
> hobby/development-mode apps. So this app is the **system of record** for your
> ratings and lists — much like Letterboxd is for films — and uses Spotify
> read-only: login, catalog search, and viewing your existing saved albums.
