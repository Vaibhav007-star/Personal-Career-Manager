"""Create tables and apply the local schema version."""

from __future__ import annotations

from database.engine import get_engine
from database.models import Base
from database.crud import SCHEMA_VERSION, get_or_create_schema_meta
from database.session import configure_session, session_scope
from utils.logging_config import get_logger

logger = get_logger("career_os.db")


def init_database(engine=None) -> None:
    engine = engine or get_engine()
    Base.metadata.create_all(engine)
    configure_session(engine)
    with session_scope() as session:
        meta = get_or_create_schema_meta(session)
        logger.info("Database ready (schema %s)", meta.schema_version or SCHEMA_VERSION)


if __name__ == "__main__":
    init_database()
    print("Database initialized.")
