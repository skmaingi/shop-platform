from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from src.db.sql import get_db
from src.products.models import Product
from src.sales.models import Sale
from src.sales.schemas import SaleCreate, SaleOut
from src.messaging.rabbitmq import publish_event
from src.auth.utils import require_role

router = APIRouter(tags=["Sales"])

##########################
# Sales
##########################
@router.post("/sales", response_model=SaleOut)
def create_sale(
    req: SaleCreate,
    db: Session = Depends(get_db),
    claims=Depends(require_role("admin", "manager", "cashier")),
):
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < req.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    amount = float(req.amount) if req.amount is not None else float(product.price) * int(req.quantity)

    product.stock -= int(req.quantity)
    sale = Sale(
        product_id=product.id,
        quantity=int(req.quantity),
        amount=amount,
        created_by_user_id=claims["sub"],
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)

    try:
        publish_event("sale.created", {
            "sale_id": sale.id,
            "product_id": sale.product_id,
            "quantity": sale.quantity,
            "amount": sale.amount,
            "created_by_user_id": sale.created_by_user_id,
            "created_at": sale.created_at.isoformat(),
        })
    except Exception:
        pass

    return sale
