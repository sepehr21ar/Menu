from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE
from app.repository.image_repository import create_uploaded_image


async def save_image(
    db: Session,
    file: UploadFile | None,
):
    if file is None:
        return None

    if not file.filename:
        return None

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Unsupported image format.")

    data = await file.read()
    if not data:
        return None

    if len(data) > MAX_IMAGE_SIZE:
        raise ValueError("Image is too large.")

    image = create_uploaded_image(
        db=db,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    return f"/api/images/{image.id}"
