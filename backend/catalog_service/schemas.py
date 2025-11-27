from pydantic import BaseModel, Field
from typing import Optional


class ProductBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    stock: int = Field(..., ge=0)
    seller_id: int = Field(..., ge=1)
    image_url: Optional[str] = None 


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)


class ProductOut(ProductBase):
    id: int

    class Config:
        from_attributes = True
