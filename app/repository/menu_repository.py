from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.models import Menu, Category


def create_menu(db: Session, owner_id: int, title: str, slug: str, currency: str):

    menu = Menu(owner_id=owner_id, title=title, slug=slug, currency=currency)

    db.add(menu)

    db.commit()

    db.refresh(menu)

    return menu


def get_menu_by_id(db: Session, menu_id: int, load_categories: bool = False):

    stmt = select(Menu).where(Menu.id == menu_id)

    if load_categories:

        stmt = stmt.options(selectinload(Menu.categories).selectinload(Category.items))

    return db.scalar(stmt)


def get_menu_by_slug(db: Session, slug: str, load_categories: bool = False):

    stmt = select(Menu).where(Menu.slug == slug)

    if load_categories:

        stmt = stmt.options(selectinload(Menu.categories).selectinload(Category.items))

    return db.scalar(stmt)


def get_menus_by_owner(db: Session, owner_id: int):

    stmt = (
        select(Menu).where(Menu.owner_id == owner_id).order_by(Menu.created_at.desc())
    )

    return list(db.scalars(stmt))


def get_published_menus_by_owner(db: Session, owner_id: int):
    stmt = (
        select(Menu)
        .where(Menu.owner_id == owner_id, Menu.is_published.is_(True))
        .order_by(Menu.created_at.desc())
    )
    return list(db.scalars(stmt))


def update_menu_settings(
    db: Session,
    menu_id: int,
    title: str,
    currency: str,
    is_published: bool,
    logo_path: str | None,
    background_image_path: str | None,
    qr_image_path: str | None,
):

    menu = get_menu_by_id(db, menu_id)

    if menu is None:
        return None

    menu.title = title
    menu.currency = currency
    menu.is_published = is_published

    if logo_path:
        menu.logo_path = logo_path

    if background_image_path:
        menu.background_image_path = background_image_path

    if qr_image_path:
        menu.qr_image_path = qr_image_path

    db.commit()
    db.refresh(menu)

    return menu
