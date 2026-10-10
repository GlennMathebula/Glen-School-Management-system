from sqlalchemy.engine import URL, make_url
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings

def _create_database_engine():
    # Prefer the configured PostgreSQL driver.
    # If Windows Application Control blocks psycopg's native pq wrapper,
    # fall back to pg8000, which is a pure-Python PostgreSQL driver.
    try:
        return create_engine(
            settings.database_url,
            pool_pre_ping=True,
        )

    except ImportError as error:
        message = str(error).lower()

        if not any(
            marker in message
            for marker in (
                "psycopg",
                "pq wrapper",
                "libpq",
            )
        ):
            raise

        configured_url = make_url(
            settings.database_url
        )

        query = dict(
            configured_url.query
        )

        sslmode = str(
            query.pop(
                "sslmode",
                "",
            )
        ).lower()

        fallback_url = URL.create(
            drivername="postgresql+pg8000",
            username=configured_url.username,
            password=configured_url.password,
            host=configured_url.host,
            port=configured_url.port,
            database=configured_url.database,
            query=query,
        )

        connect_args = {}

        if sslmode in {
            "require",
            "verify-ca",
            "verify-full",
        }:
            connect_args[
                "ssl_context"
            ] = True

        return create_engine(
            fallback_url,
            pool_pre_ping=True,
            connect_args=connect_args,
        )


engine = _create_database_engine()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar()