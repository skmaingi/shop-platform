from fastapi import FastAPI

from src.db.sql import engine, Base

from src.auth.routers import router as auth_router
from src.products.routers import router as products_router
from src.sales.routers import router as sales_router
from src.users.routers import router as users_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shop Backend (JWT + Refresh + Logout + Products + Sales + Users + RabbitMQ)")

# Register all routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(sales_router)
app.include_router(users_router)

@app.get("/health")
def health():
    return {"status": "ok"}