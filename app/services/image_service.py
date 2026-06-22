from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE, UPLOAD_DIR

IMAGE_DIR = UPLOAD_DIR / "images"

IMAGE_DIR.mkdir(exist_ok=True, parents=True)


async def save_image(
    file: UploadFile | None,
):

    if file is None:
        return None

    suffix = Path(file.filename).suffix.lower()

    if suffix not in ALLOWED_IMAGE_EXTENSIONS:

        raise ValueError("Unsupported image format.")

    data = await file.read()

    if len(data) > MAX_IMAGE_SIZE:

        raise ValueError("Image is too large.")

    filename = uuid4().hex + suffix

    filepath = IMAGE_DIR / filename

    with open(filepath, "wb") as f:

        f.write(data)

    return "/static/uploads/images/" + filename
