from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SaleCreate(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)
    amount: Optional[float] = None

class SaleOut(BaseModel):
    id: str
    product_id: str
    quantity: int
    amount: float
    created_at: datetime
    created_by_user_id: str

    class Config:
        from_attributes = True