import re
from unidecode import unidecode


def slugify(text: str):

    text = unidecode(text)

    text = text.lower()

    text = re.sub(r"[^a-z0-9]+", "-", text)

    text = text.strip("-")

    return text
