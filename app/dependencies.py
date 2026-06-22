from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.repository.owner_repository import get_owner_by_id
from app.security import SESSION_COOKIE, verify_session


def current_owner(
    menu_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_db),
):

    if menu_session is None:
        return None

    owner_id = verify_session(menu_session)

    if owner_id is None:
        return None

    return get_owner_by_id(db, owner_id)


def require_owner(owner=Depends(current_owner)):

    if owner is None:

        raise HTTPException(status_code=401, detail="Not authenticated")

    return owner
