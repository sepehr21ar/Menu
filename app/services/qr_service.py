from pathlib import Path

import qrcode

from app.config import UPLOAD_DIR

QR_DIR = UPLOAD_DIR / "qr"

QR_DIR.mkdir(exist_ok=True, parents=True)


def generate_qr_image(
    url: str,
):

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )

    qr.add_data(url)

    qr.make(fit=True)

    image = qr.make_image()

    filename = url.split("/")[-1] + ".png"

    path = QR_DIR / filename

    image.save(path)

    return "/static/uploads/qr/" + filename
