from fastapi import APIRouter, Depends, Form, HTTPException, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies import current_owner
from app.schemas import OwnerResponse, TokenResponse
from app.security import SESSION_COOKIE, sign_session
from app.services.auth_service import authenticate_owner, register_owner

router = APIRouter(tags=["Auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(
    response: Response,
    restaurant_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        owner = register_owner(db, restaurant_name, email, password)
    except ValueError:
        raise HTTPException(status_code=400, detail="این ایمیل قبلا ثبت شده است.")

    response.set_cookie(
        key=SESSION_COOKIE,
        value=sign_session(owner.id),
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=60 * 60 * 24 * 7,
    )
    return {"message": "ثبت‌نام با موفقیت انجام شد."}


@router.post("/login", response_model=TokenResponse)
def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    owner = authenticate_owner(db, email, password)
    if not owner:
        raise HTTPException(status_code=401, detail="ایمیل یا رمز عبور اشتباه است.")

    response.set_cookie(
        key=SESSION_COOKIE,
        value=sign_session(owner.id),
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=60 * 60 * 24 * 7,
    )
    return {"message": "ورود با موفقیت انجام شد."}


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=OwnerResponse)
def me(owner=Depends(current_owner)):
    if owner is None:
        raise HTTPException(status_code=401, detail="وارد حساب نشده‌اید.")
    return owner
