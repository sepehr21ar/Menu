from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.repository.menu_repository import get_published_menus_by_owner
from app.schemas import MenuResponse, PublicMenuSummary
from app.services.menu_service import build_public_menu_view

router = APIRouter(tags=["Public"])


@router.get("/m/{slug}", response_model=MenuResponse)
def public_menu(slug: str, db: Session = Depends(get_db)):
    menu = build_public_menu_view(db, slug)
    if menu is None:
        raise HTTPException(status_code=404, detail="منو پیدا نشد.")
    return menu


@router.get("/restaurants/{owner_id}/menus", response_model=list[PublicMenuSummary])
def public_restaurant_menus(owner_id: int, db: Session = Depends(get_db)):
    return get_published_menus_by_owner(db, owner_id)
