from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int = 0

class ProductOut(BaseModel):
    id: str
    name: str
    price: float
    stock: int

    class Config:
        from_attributes = True
