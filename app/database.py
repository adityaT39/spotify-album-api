"""Database engine, session factory, and the declarative base for models."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# SQLite needs this flag when used with FastAPI's threaded request handling.
# Other databases (e.g. PostgreSQL) don't, so we only set it for SQLite.
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Parent class every ORM model inherits from."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that hands a database session to a request and
    guarantees it is closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
