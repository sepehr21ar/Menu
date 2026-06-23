from pydantic import BaseModel
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class MenuItemBase(BaseModel):
    name: str
    details: Optional[str] = ""
    price: str
    image_path: Optional[str] = None
    is_available: bool = True


class MenuItemResponse(MenuItemBase):

    model_config = ConfigDict(from_attributes=True)

    id: int

    category_id: int


class CategoryBase(BaseModel):
    name: str
    image_path: Optional[str] = None


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    position: int
    items: List[MenuItemResponse] = Field(default_factory=list)


class MenuBase(BaseModel):
    title: str
    currency: str = "$"


class MenuResponse(MenuBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    logo_path: Optional[str] = None
    qr_image_path: Optional[str] = None
    is_published: bool
    categories: List[CategoryResponse] = Field(default_factory=list)


class OwnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    restaurant_name: str
    email: str


class TokenResponse(BaseModel):
    message: str
