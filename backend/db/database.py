# db/database.py
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from ..core.config import settings

# Pulls the safely parsed URL from our centralized config
engine = create_engine(settings.DATABASE_URL)

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