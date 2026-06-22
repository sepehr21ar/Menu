from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas import MenuResponse
from app.services.menu_service import build_public_menu_view

router = APIRouter(tags=["Public"])


@router.get("/m/{slug}", response_model=MenuResponse)
def public_menu(slug: str, db: Session = Depends(get_db)):
    menu = build_public_menu_view(db, slug)
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu
