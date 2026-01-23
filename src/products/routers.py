from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from src.db.sql import get_db
from src.products.models import Product
from src.products.schemas import ProductCreate, ProductOut
from src.auth.utils import require_role, get_current_claims

router = APIRouter(tags=["Products"])

##########################
# Products
##########################
@router.post("/products", response_model=ProductOut)
def create_product(
    req: ProductCreate,
    db: Session = Depends(get_db),
    _claims=Depends(require_role("admin", "manager")),
):
    p = Product(name=req.name, price=req.price, stock=req.stock)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@router.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db), _claims=Depends(get_current_claims)):
    return db.query(Product).all()
