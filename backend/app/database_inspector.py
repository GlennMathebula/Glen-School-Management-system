from sqlalchemy import inspect

from app.database import engine


def get_database_tables():
    inspector = inspect(engine)

    return inspector.get_table_names()