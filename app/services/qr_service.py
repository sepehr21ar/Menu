from io import BytesIO

import qrcode
from fastapi import Request

from app.config import PUBLIC_BASE_URL


def public_menu_url(request: Request, slug: str) -> str:
    if PUBLIC_BASE_URL:
        return f"{PUBLIC_BASE_URL}/m/{slug}"

    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}/m/{slug}"

    return str(request.url_for("public_page", slug=slug))


def generate_qr_png(url: str) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
