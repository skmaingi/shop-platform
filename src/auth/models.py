import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.db.sql import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # token id (jti)
    user_id = Column(String, ForeignKey("system_users.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False)  # hashed refresh token secret
    created_at = Column(DateTime, default=timezone.utc)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("SystemUser")
