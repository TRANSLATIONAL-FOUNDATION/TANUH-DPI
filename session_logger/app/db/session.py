import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

logger = logging.getLogger(__name__)

connect_args = {}
USE_SQLITE = False


def _is_valid_file(path: str) -> bool:
    return bool(path and os.path.isfile(path) and os.path.getsize(path) > 10)


if settings.MYSQL_USER and settings.MYSQL_PASSWORD:
    ssl_config = {}
    if settings.MYSQL_SSL_CA and _is_valid_file(settings.MYSQL_SSL_CA):
        ssl_config["ca"] = settings.MYSQL_SSL_CA
    if settings.MYSQL_SSL_CERT and _is_valid_file(settings.MYSQL_SSL_CERT):
        ssl_config["cert"] = settings.MYSQL_SSL_CERT
    if settings.MYSQL_SSL_KEY and _is_valid_file(settings.MYSQL_SSL_KEY):
        ssl_config["key"] = settings.MYSQL_SSL_KEY
    connect_args["ssl"] = ssl_config
    if ssl_config:
        ssl_config["check_hostname"] = False
    db_url = settings.DATABASE_URL
    logger.info("Using MySQL: %s", settings.MYSQL_HOST)
else:
    USE_SQLITE = True
    _db_dir = os.environ.get('SQLITE_DATA_DIR', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    os.makedirs(_db_dir, exist_ok=True)
    _db_path = os.path.join(_db_dir, "local_session.db")
    db_url = f"sqlite:///{_db_path}"
    connect_args = {"check_same_thread": False}
    logger.info("MySQL credentials not found — using local SQLite: %s", _db_path)

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
