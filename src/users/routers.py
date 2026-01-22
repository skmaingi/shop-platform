from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from src.db.sql import get_db
from src.users.models import SystemUser
from src.users.schemas import UserCreate, UserUpdate, UserOut
from src.auth.utils import hash_password, require_role

router = APIRouter(tags=["Users"])

##########################
# User Management (Admin)
##########################
@router.post("/system/admin", response_model=UserOut)
def system_admin(db: Session = Depends(get_db)):
    existing_admin = db.query(SystemUser).filter(SystemUser.role == "admin").first()
    if existing_admin:
        return existing_admin
    admin = SystemUser(
        username="admin",
        password_hash=hash_password("admin123"),
        role="admin",
        full_name="Default Admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

@router.post("/users", response_model=UserOut)
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    _claims=Depends(require_role("admin")),
):
    if db.query(SystemUser).filter(SystemUser.username == req.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = SystemUser(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role,
        full_name=req.full_name,
        is_active=req.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _claims=Depends(require_role("admin")),
):
    return db.query(SystemUser).order_by(SystemUser.created_at.desc()).all()

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    req: UserUpdate,
    db: Session = Depends(get_db),
    _claims=Depends(require_role("admin")),
):
    user = db.query(SystemUser).filter(SystemUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.role is not None:
        user.role = req.role
    if req.full_name is not None:
        user.full_name = req.full_name
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.password is not None:
        user.password_hash = hash_password(req.password)

    db.commit()
    db.refresh(user)
    return user
