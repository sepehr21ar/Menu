from fastapi import HTTPException


def validate_title(
    title: str,
):

    title = title.strip()

    if len(title) < 2:

        raise HTTPException(400, "عنوان خیلی کوتاه است.")

    return title


def validate_currency(
    currency: str,
):

    currency = currency.strip()

    if currency == "":
        currency = "$"

    return currency
