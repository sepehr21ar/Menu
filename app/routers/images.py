from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.repository.image_repository import get_uploaded_image

router = APIRouter(tags=["Images"])


@router.get("/images/{image_id}")
def serve_uploaded_image(image_id: int, db: Session = Depends(get_db)):
    image = get_uploaded_image(db, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(
        content=image.data,
        media_type=image.content_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
