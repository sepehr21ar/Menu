from app.database.database import Base, engine
from app import models


def init_db():
    Base.metadata.create_all(engine)
    print("Database is ready.")
