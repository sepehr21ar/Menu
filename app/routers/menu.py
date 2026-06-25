from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies import require_owner
from app.repository.category_repository import (
    create_category,
    delete_category,
    get_category_by_id,
    get_categories_by_menu,
    update_category_image,
)
from app.repository.item_repository import create_item, delete_item, get_item_by_id
from app.repository.menu_repository import get_menu_by_id, update_menu_settings
from app.schemas import CategoryResponse, MenuItemResponse, MenuResponse
from app.services.image_service import save_image
from app.services.qr_service import generate_qr_png, public_menu_url

router = APIRouter(tags=["Menu"])


def ensure_owner_menu(db: Session, menu_id: int, owner):
    menu = get_menu_by_id(db, menu_id, load_categories=True)
    if menu is None or menu.owner_id != owner.id:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu


@router.get("/menus/{menu_id}", response_model=MenuResponse)
def get_menu_for_edit(
    menu_id: int,
    owner=Depends(require_owner),
    db: Session = Depends(get_db),
):
    return ensure_owner_menu(db, menu_id, owner)


@router.put("/menus/{menu_id}", response_model=MenuResponse)
async def update_menu_settings_api(
    request: Request,
    menu_id: int,
    title: str = Form(...),
    currency: str = Form(...),
    is_published: bool = Form(False),
    logo: UploadFile = File(None),
    background_image: UploadFile = File(None),
    qr_image: UploadFile = File(None),
    owner=Depends(require_owner),
    db: Session = Depends(get_db),
):
    menu = ensure_owner_menu(db, menu_id, owner)

    try:
        logo_path = await save_image(db, logo)
        background_image_path = await save_image(db, background_image)
        qr_path = await save_image(db, qr_image)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if qr_path is None and not menu.qr_image_path:
        qr_path = f"/api/menus/{menu.id}/qr"

    updated_menu = update_menu_settings(
        db=db,
        menu_id=menu_id,
        title=title.strip(),
        currency=currency.strip() or "$",
        is_published=is_published,
        logo_path=logo_path,
        background_image_path=background_image_path,
        qr_image_path=qr_path,
    )
    return get_menu_by_id(db, updated_menu.id, load_categories=True)


@router.get("/menus/{menu_id}/qr")
def get_menu_qr_image(
    request: Request,
    menu_id: int,
    owner=Depends(require_owner),
    db: Session = Depends(get_db),
):
    menu = ensure_owner_menu(db, menu_id, owner)
    url = public_menu_url(request, menu.slug)
    return Response(content=generate_qr_png(url), media_type="image/png")


@router.post(
    "/menus/{menu_id}/categories", response_model=CategoryResponse, status_code=201
)
async def add_category_api(
    menu_id: int,
    name: str = Form(...),
    image: UploadFile = File(None),
    owner=Depends(require_owner),
    db: Session = Depends(get_db),
):
    ensure_owner_menu(db, menu_id, owner)

    try:
        image_path = await save_image(db, image)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    position = len(get_categories_by_menu(db, menu_id))
    category = create_category(
        db, menu_id=menu_id, name=name.strip(), position=position
    )
    if image_path:
        category = update_category_image(db, category, image_path)
    return category


@router.delete("/categories/{category_id}", status_code=204)
def delete_category_api(
    category_id: int,
    owner=Depends(require_owner),
    db: Session = Depends(get_db),
):
    category = get_category_by_id(db, category_id)
    if category is None or category.menu.owner_id != owner.id:
        raise HTTPException(status_code=404, detail="Category not found")
    delete_category(db, category)


@router.post(
    "/categories/{category_id}/items", response_model=MenuItemResponse, status_code=201
)
async def add_item_api(
    category_id: int,
    name: str = Form(...),
    details: str = Form(""),
    price: str = Form(...),
    image: UploadFile = File(None),
    owner=Depends(require_owner),
    db: Session = Depends(get_db),
):
    category = get_category_by_id(db, category_id)
    if category is None or category.menu.owner_id != owner.id:
        raise HTTPException(status_code=404, detail="Category not found")

    try:
        image_path = await save_image(db, image)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return create_item(
        db,
        category_id=category_id,
        name=name.strip(),
        details=details.strip(),
        price=price.strip(),
        image_path=image_path,
    )


@router.delete("/items/{item_id}", status_code=204)
def delete_item_api(
    item_id: int,
    owner=Depends(require_owner),
    db: Session = Depends(get_db),
):
    item = get_item_by_id(db, item_id)
    if item is None or item.category.menu.owner_id != owner.id:
        raise HTTPException(status_code=404, detail="Item not found")
    delete_item(db, item)
