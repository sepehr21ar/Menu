from uuid import uuid4

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies import require_owner
from app.repository.menu_repository import create_menu, get_menus_by_owner
from app.schemas import MenuResponse
from app.services.validation_service import validate_currency, validate_title
from app.utils import slugify

router = APIRouter(tags=["Dashboard"])


@router.get("/menus", response_model=list[MenuResponse])
def get_user_menus(owner=Depends(require_owner), db: Session = Depends(get_db)):
    return get_menus_by_owner(db, owner.id)


@router.post("/menus", response_model=MenuResponse, status_code=201)
def create_new_menu(
    request: Request,
    title: str = Form(...),
    currency: str = Form("$"),
    owner=Depends(require_owner),
    db: Session = Depends(get_db),
):
    clean_title = validate_title(title)
    clean_currency = validate_currency(currency)
    base_slug = slugify(f"{owner.restaurant_name}-{clean_title}")
    slug = f"{base_slug}-{uuid4().hex[:8]}"

    menu = create_menu(
        db=db,
        owner_id=owner.id,
        title=clean_title,
        slug=slug,
        currency=clean_currency,
    )

    menu.qr_image_path = f"/api/menus/{menu.id}/qr"
    db.commit()
    db.refresh(menu)
    return menu
