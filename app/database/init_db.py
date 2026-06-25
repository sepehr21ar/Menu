from sqlalchemy import inspect, text

from app import models
from app.database.database import Base, engine


def add_column_if_missing(table_name: str, column_name: str, ddl: str):
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name not in columns:
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def init_db():
    Base.metadata.create_all(engine)
    add_column_if_missing(
        "menus",
        "background_image_path",
        "background_image_path VARCHAR(255)",
    )
    print("Database is ready.")
