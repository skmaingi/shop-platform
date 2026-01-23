import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.db.sql import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
