from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from ..core.config import settings


def _normalize_database_url(url: str) -> str:
    """
    Heroku add-ons (JawsDB/ClearDB) hand back 'mysql://...',
    sometimes with a '?reconnect=true' query string. SQLAlchemy
    needs an explicit driver, and doesn't understand that query param.
    """
    if url.startswith("mysql://"):
        url = url.replace("mysql://", "mysql+pymysql://", 1)
    elif url.startswith("mysql2://"):
        url = url.replace("mysql2://", "mysql+pymysql://", 1)

    if "?" in url:
        url = url.split("?", 1)[0]

    return url


SQLALCHEMY_DATABASE_URL = _normalize_database_url(settings.DATABASE_URL)

# pool_pre_ping avoids "MySQL server has gone away" errors on Heroku,
# where idle connections get dropped by the add-on after a timeout.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=280,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session scoped to a single request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()