import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.db.sql import Base


class Sale(Base):
    __tablename__ = "sales"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=timezone.utc)
    created_by_user_id = Column(String, ForeignKey("system_users.id"), nullable=False)

    product = relationship("Product")
    created_by = relationship("SystemUser")