from sqlalchemy.orm import Session

from app.models import UploadedImage


def create_uploaded_image(
    db: Session,
    filename: str,
    content_type: str,
    data: bytes,
) -> UploadedImage:
    image = UploadedImage(
        filename=filename,
        content_type=content_type,
        data=data,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def get_uploaded_image(db: Session, image_id: int) -> UploadedImage | None:
    return db.get(UploadedImage, image_id)
