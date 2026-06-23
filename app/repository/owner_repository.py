from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Owner


def get_owner_by_id(db: Session, owner_id: int):

    return db.scalar(select(Owner).where(Owner.id == owner_id))


def get_owner_by_email(db: Session, email: str):

    return db.scalar(select(Owner).where(Owner.email == email))


def create_owner(db: Session, restaurant_name: str, email: str, password_hash: str):

    owner = Owner(
        restaurant_name=restaurant_name, email=email, password_hash=password_hash
    )

    db.add(owner)

    db.commit()

    db.refresh(owner)

    return owner
