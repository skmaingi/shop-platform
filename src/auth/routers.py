from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.db.sql import get_db
from src.users.models import SystemUser
from src.auth.models import RefreshToken
from src.auth.schemas import (
    LoginRequest, TokenResponse, RefreshRequest, LogoutRequest,
)
from src.auth.utils import (
    verify_password, create_access_token,
    get_current_claims, require_role,
    new_refresh_pair, pack_refresh_token, unpack_refresh_token,
    hash_refresh_secret, verify_refresh_secret,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

##########################
# Authentication
##########################
@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(SystemUser).filter(SystemUser.username == req.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(sub=user.id, role=user.role)

    jti, secret, expires_at = new_refresh_pair()
    rt = RefreshToken(
        id=jti,
        user_id=user.id,
        token_hash=hash_refresh_secret(secret),
        expires_at=expires_at,
        revoked_at=None,
    )
    db.add(rt)
    db.commit()

    refresh = pack_refresh_token(jti, secret)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    try:
        jti, secret = unpack_refresh_token(req.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    rt = db.query(RefreshToken).filter(RefreshToken.id == jti).first()
    if not rt or rt.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Refresh token revoked or not found")
    if rt.expires_at <= timezone.utc():
        raise HTTPException(status_code=401, detail="Refresh token expired")
    if not verify_refresh_secret(secret, rt.token_hash):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(SystemUser).filter(SystemUser.id == rt.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive")

    # ROTATION: revoke old refresh token and issue a new one
    rt.revoked_at = timezone.utc()
    db.commit()

    access = create_access_token(sub=user.id, role=user.role)
    new_jti, new_secret, new_expires_at = new_refresh_pair()
    new_rt = RefreshToken(
        id=new_jti,
        user_id=user.id,
        token_hash=hash_refresh_secret(new_secret),
        expires_at=new_expires_at,
        revoked_at=None,
    )
    db.add(new_rt)
    db.commit()

    refresh_token = pack_refresh_token(new_jti, new_secret)
    return {"access_token": access, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/logout")
def logout(req: LogoutRequest, db: Session = Depends(get_db)):
    # Logout = revoke the provided refresh token (access tokens expire quickly)
    try:
        jti, _secret = unpack_refresh_token(req.refresh_token)
    except ValueError:
        # Don't leak info; logout should be idempotent
        return {"status": "ok"}

    rt = db.query(RefreshToken).filter(RefreshToken.id == jti).first()
    if rt and rt.revoked_at is None:
        rt.revoked_at = timezone.utc()
        db.commit()
    return {"status": "ok"}

@router.get("/me", response_model=dict)
def me(claims=Depends(get_current_claims)):
    return {"user_id": claims["sub"], "role": claims.get("role")}
