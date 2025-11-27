from sqlalchemy import Column, Integer, String, Float, Text
from .db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    seller_id = Column(Integer, nullable=False)
    image_url = Column(String(500), nullable=True)
