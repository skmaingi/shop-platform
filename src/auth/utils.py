from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import uuid

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_refresh_secret(secret: str) -> str:
    # bcrypt-hash the refresh token secret so DB leak doesn't expose usable tokens
    return pwd_context.hash(secret)

def verify_refresh_secret(secret: str, hashed: str) -> bool:
    return pwd_context.verify(secret, hashed)

def create_access_token(sub: str, role: str) -> str:
    expire = timezone.utc() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": sub, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def get_current_claims(
    cred: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = decode_jwt(cred.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_role(*roles: str):
    def dep(claims=Depends(get_current_claims)):
        if claims.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return claims
    return dep

def new_refresh_pair() -> tuple[str, str, datetime]:
    """Returns (jti, secret, expires_at). Client holds 'jti.secret' as refresh_token."""
    jti = str(uuid.uuid4())
    secret = str(uuid.uuid4()) + str(uuid.uuid4())
    expires_at = timezone.utc() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return jti, secret, expires_at

def pack_refresh_token(jti: str, secret: str) -> str:
    return f"{jti}.{secret}"

def unpack_refresh_token(token: str) -> tuple[str, str]:
    if "." not in token:
        raise ValueError("Malformed refresh token")
    jti, secret = token.split(".", 1)
    if not jti or not secret:
        raise ValueError("Malformed refresh token")
    return jti, secret