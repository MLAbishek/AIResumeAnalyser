from sqlalchemy import text

from app.database.connection import engine


def test_postgresql_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        assert result.scalar() == 1