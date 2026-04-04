from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_sqlalchemy_engine(database_url: str) -> Engine:
    return create_engine(database_url, future=True, pool_pre_ping=True)


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_sqlalchemy_engine(database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
