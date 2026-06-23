from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MenuItem


def create_item(
    db: Session,
    category_id: int,
    name: str,
    details: str,
    price: str,
    image_path: str | None = None,
):

    item = MenuItem(
        category_id=category_id,
        name=name,
        details=details,
        price=price,
        image_path=image_path,
    )

    db.add(item)

    db.commit()

    db.refresh(item)

    return item


def get_item_by_id(db: Session, item_id: int):

    return db.scalar(select(MenuItem).where(MenuItem.id == item_id))


def delete_item(db: Session, item: MenuItem):

    db.delete(item)

    db.commit()
