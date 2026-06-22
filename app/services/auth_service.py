from sqlalchemy.orm import Session

from app.repository.owner_repository import (
    create_owner,
    get_owner_by_email,
)

from app.security import (
    hash_password,
    verify_password,
)


def register_owner(
    db: Session,
    restaurant_name: str,
    email: str,
    password: str,
):

    email = email.lower().strip()

    if get_owner_by_email(db, email):

        raise ValueError("Email already exists")

    owner = create_owner(
        db=db,
        restaurant_name=restaurant_name.strip(),
        email=email,
        password_hash=hash_password(password),
    )

    return owner


def authenticate_owner(
    db: Session,
    email: str,
    password: str,
):

    owner = get_owner_by_email(db, email.lower().strip())

    if owner is None:
        return None

    if not verify_password(password, owner.password_hash):
        return None

    return owner
