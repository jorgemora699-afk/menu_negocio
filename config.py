import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


def _database_uri():
    """Normaliza DATABASE_URL para usar siempre el driver psycopg2."""
    uri = os.getenv("DATABASE_URL", "")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql+psycopg2://", 1)
    elif uri.startswith("postgresql://"):
        uri = uri.replace("postgresql://", "postgresql+psycopg2://", 1)
    return uri


class Config:
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
