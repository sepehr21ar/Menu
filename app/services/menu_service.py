from sqlalchemy.orm import Session

from app.repository.menu_repository import (
    get_menu_by_slug,
)


def build_public_menu_view(
    db: Session,
    slug: str,
):

    menu = get_menu_by_slug(db, slug, load_categories=True)

    if menu is None:
        return None

    if not menu.is_published:
        return None

    return menu
