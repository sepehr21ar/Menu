from pathlib import Path
from uuid import uuid4
import re

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.database import Base, engine, get_db
from app.models import Category, Menu, MenuItem, Owner
from app.qr import make_qr_svg
from app.security import SESSION_COOKIE, hash_password, read_session, sign_session, verify_password


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

Base.metadata.create_all(bind=engine)


def ensure_schema() -> None:
    with engine.begin() as connection:
        menu_columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(menus)")).fetchall()
        }
        category_columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(categories)")).fetchall()
        }
        if "logo_path" not in menu_columns:
            connection.execute(text("ALTER TABLE menus ADD COLUMN logo_path VARCHAR(255)"))
        if "image_path" not in category_columns:
            connection.execute(text("ALTER TABLE categories ADD COLUMN image_path VARCHAR(255)"))


ensure_schema()

app = FastAPI(title="Menu Maker")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def format_price(value: str | int | float | None) -> str:
    if value is None:
        return ""
    raw = str(value).strip()
    compact = raw.replace(",", "").replace(" ", "")
    if not compact:
        return raw
    if re.fullmatch(r"\d+", compact):
        return f"{int(compact):,}"
    if re.fullmatch(r"\d+\.\d+", compact):
        number = float(compact)
        return f"{number:,.2f}".rstrip("0").rstrip(".")
    return raw


def category_cover(category: Category) -> str | None:
    if category.image_path:
        return category.image_path
    for item in category.items:
        if item.image_path:
            return item.image_path
    return None


templates.env.filters["price"] = format_price
templates.env.globals["category_cover"] = category_cover


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "menu"


def flash_redirect(url: str, message: str | None = None) -> RedirectResponse:
    response = RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)
    if message:
        response.set_cookie("flash", message, max_age=8, httponly=True, samesite="lax")
    return response


def current_owner(request: Request, db: Session) -> Owner | None:
    owner_id = read_session(request.cookies.get(SESSION_COOKIE))
    if owner_id is None:
        return None
    return db.get(Owner, owner_id)


def require_owner(request: Request, db: Session = Depends(get_db)) -> Owner:
    owner = current_owner(request, db)
    if owner is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return owner


def render(request: Request, template: str, context: dict, status_code: int = 200) -> HTMLResponse:
    context["request"] = request
    context["owner"] = context.get("owner")
    context["flash"] = request.cookies.get("flash")
    response = templates.TemplateResponse(request, template, context, status_code=status_code)
    if request.cookies.get("flash"):
        response.delete_cookie("flash")
    return response


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    owner = current_owner(request, db)
    if owner:
        return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return render(request, "home.html", {"owner": None})


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return render(request, "signup.html", {"owner": current_owner(request, db)})


@app.post("/signup")
def signup(
    restaurant_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    exists = db.scalar(select(Owner).where(Owner.email == email.lower().strip()))
    if exists:
        return flash_redirect("/signup", "An account with that email already exists.")
    owner = Owner(
        restaurant_name=restaurant_name.strip(),
        email=email.lower().strip(),
        password_hash=hash_password(password),
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    response = flash_redirect("/dashboard", "Welcome. Your restaurant workspace is ready.")
    response.set_cookie(SESSION_COOKIE, sign_session(owner.id), httponly=True, samesite="lax")
    return response


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return render(request, "login.html", {"owner": current_owner(request, db)})


@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)) -> RedirectResponse:
    owner = db.scalar(select(Owner).where(Owner.email == email.lower().strip()))
    if owner is None or not verify_password(password, owner.password_hash):
        return flash_redirect("/login", "Email or password is not correct.")
    response = flash_redirect("/dashboard", "Signed in.")
    response.set_cookie(SESSION_COOKIE, sign_session(owner.id), httponly=True, samesite="lax")
    return response


@app.post("/logout")
def logout() -> RedirectResponse:
    response = flash_redirect("/", "Signed out.")
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, owner: Owner = Depends(require_owner), db: Session = Depends(get_db)) -> HTMLResponse:
    menus = db.scalars(
        select(Menu)
        .where(Menu.owner_id == owner.id)
        .order_by(Menu.created_at.desc())
        .options(selectinload(Menu.categories))
    ).all()
    return render(request, "dashboard.html", {"owner": owner, "menus": menus})


@app.post("/menus")
def create_menu(
    title: str = Form(...),
    currency: str = Form("$"),
    owner: Owner = Depends(require_owner),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    base_slug = slugify(f"{owner.restaurant_name}-{title}")
    slug = f"{base_slug}-{uuid4().hex[:6]}"
    menu = Menu(owner_id=owner.id, title=title.strip(), currency=currency.strip() or "$", slug=slug)
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return flash_redirect(f"/menus/{menu.id}/edit", "Menu created. Add your first category.")


@app.get("/menus/{menu_id}/edit", response_class=HTMLResponse)
def edit_menu(
    menu_id: int,
    request: Request,
    owner: Owner = Depends(require_owner),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    menu = get_owner_menu(menu_id, owner, db)
    public_url = str(request.url_for("public_menu", slug=menu.slug))
    return render(request, "edit_menu.html", {"owner": owner, "menu": menu, "public_url": public_url})


@app.post("/menus/{menu_id}/settings")
async def update_menu_settings(
    menu_id: int,
    title: str = Form(...),
    currency: str = Form(...),
    is_published: bool = Form(False),
    logo: UploadFile | None = File(None),
    owner: Owner = Depends(require_owner),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    menu = get_owner_menu(menu_id, owner, db)
    menu.title = title.strip()
    menu.currency = currency.strip() or "$"
    menu.is_published = is_published
    logo_path = await save_image(logo)
    if logo_path:
        menu.logo_path = logo_path
    db.commit()
    return flash_redirect(f"/menus/{menu.id}/edit", "Menu settings saved.")


@app.post("/menus/{menu_id}/categories")
async def add_category(
    menu_id: int,
    name: str = Form(...),
    image: UploadFile | None = File(None),
    owner: Owner = Depends(require_owner),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    menu = get_owner_menu(menu_id, owner, db)
    image_path = await save_image(image)
    category = Category(
        menu_id=menu.id,
        name=name.strip(),
        image_path=image_path,
        position=len(menu.categories) + 1,
    )
    db.add(category)
    db.commit()
    return flash_redirect(f"/menus/{menu.id}/edit", "Category added.")


@app.post("/categories/{category_id}/image")
async def update_category_image(
    category_id: int,
    image: UploadFile | None = File(None),
    owner: Owner = Depends(require_owner),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    category = get_owner_category(category_id, owner, db)
    image_path = await save_image(image)
    if image_path:
        category.image_path = image_path
        db.commit()
        return flash_redirect(f"/menus/{category.menu_id}/edit", "Category image updated.")
    return flash_redirect(f"/menus/{category.menu_id}/edit", "Choose an image before saving.")


@app.post("/categories/{category_id}/delete")
def delete_category(
    category_id: int,
    owner: Owner = Depends(require_owner),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    category = get_owner_category(category_id, owner, db)
    menu_id = category.menu_id
    db.delete(category)
    db.commit()
    return flash_redirect(f"/menus/{menu_id}/edit", "Category deleted.")


@app.post("/categories/{category_id}/items")
async def add_item(
    category_id: int,
    name: str = Form(...),
    price: str = Form(...),
    details: str = Form(""),
    image: UploadFile | None = File(None),
    owner: Owner = Depends(require_owner),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    category = get_owner_category(category_id, owner, db)
    image_path = await save_image(image)
    item = MenuItem(
        category_id=category.id,
        name=name.strip(),
        price=price.strip(),
        details=details.strip(),
        image_path=image_path,
    )
    db.add(item)
    db.commit()
    return flash_redirect(f"/menus/{category.menu_id}/edit", "Item added.")


@app.post("/items/{item_id}/delete")
def delete_item(
    item_id: int,
    owner: Owner = Depends(require_owner),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    item = get_owner_item(item_id, owner, db)
    menu_id = item.category.menu_id
    db.delete(item)
    db.commit()
    return flash_redirect(f"/menus/{menu_id}/edit", "Item deleted.")


@app.get("/m/{slug}", response_class=HTMLResponse)
def public_menu(slug: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    menu = db.scalar(
        select(Menu)
        .where(Menu.slug == slug)
        .options(selectinload(Menu.owner), selectinload(Menu.categories).selectinload(Category.items))
    )
    if menu is None or not menu.is_published:
        raise HTTPException(status_code=404, detail="Menu not found")
    return render(request, "public_menu.html", {"owner": None, "menu": menu})


@app.get("/m/{slug}/qr.svg")
def menu_qr(slug: str, request: Request, db: Session = Depends(get_db)) -> Response:
    menu = db.scalar(select(Menu).where(Menu.slug == slug))
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    url = str(request.url_for("public_menu", slug=menu.slug))
    return Response(content=make_qr_svg(url), media_type="image/svg+xml")


def get_owner_menu(menu_id: int, owner: Owner, db: Session) -> Menu:
    menu = db.scalar(
        select(Menu)
        .where(Menu.id == menu_id, Menu.owner_id == owner.id)
        .options(selectinload(Menu.categories).selectinload(Category.items))
    )
    if menu is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu


def get_owner_category(category_id: int, owner: Owner, db: Session) -> Category:
    category = db.scalar(
        select(Category)
        .where(Category.id == category_id)
        .join(Menu)
        .where(Menu.owner_id == owner.id)
        .options(selectinload(Category.menu), selectinload(Category.items))
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def get_owner_item(item_id: int, owner: Owner, db: Session) -> MenuItem:
    item = db.scalar(
        select(MenuItem)
        .where(MenuItem.id == item_id)
        .join(Category)
        .join(Menu)
        .where(Menu.owner_id == owner.id)
        .options(selectinload(MenuItem.category))
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


async def save_image(image: UploadFile | None) -> str | None:
    if image is None or not image.filename:
        return None
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
    suffix = Path(image.filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = ".jpg"
    filename = f"{uuid4().hex}{suffix}"
    path = UPLOAD_DIR / filename
    contents = await image.read()
    if len(contents) > 4 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 4MB.")
    path.write_bytes(contents)
    return f"/static/uploads/{filename}"
