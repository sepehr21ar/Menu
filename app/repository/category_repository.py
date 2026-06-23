from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category


def create_category(db: Session, menu_id: int, name: str, position: int):

    category = Category(menu_id=menu_id, name=name, position=position)

    db.add(category)

    db.commit()

    db.refresh(category)

    return category


def get_category_by_id(db: Session, category_id: int):

    return db.scalar(select(Category).where(Category.id == category_id))


def get_categories_by_menu(db: Session, menu_id: int):

    stmt = (
        select(Category).where(Category.menu_id == menu_id).order_by(Category.position)
    )

    return list(db.scalars(stmt))


def delete_category(db: Session, category: Category):

    db.delete(category)

    db.commit()


def update_category_image(db: Session, category: Category, image_path: str | None):

    category.image_path = image_path

    db.commit()

    db.refresh(category)

    return category
