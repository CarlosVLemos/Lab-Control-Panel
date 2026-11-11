import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


def database_url(value=None):
    url = make_url(value or os.environ["DATABASE_URL"])
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    if url.drivername != "postgresql+psycopg":
        raise ValueError("PostgreSQL with psycopg 3 is required")
    return url


def create_database_engine(value=None):
    return create_engine(database_url(value), pool_pre_ping=True)


def create_session_factory(engine):
    return sessionmaker(bind=engine)
