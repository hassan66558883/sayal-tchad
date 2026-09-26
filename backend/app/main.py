from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import SessionLocal
from app.routers import (
    audit_logs,
    auth,
    branches,
    commercial,
    containers,
    deliveries,
    finance,
    fleet,
    fleet_ops,
    hr,
    imports,
    invoices,
    partners,
    payments,
    product_catalog,
    products,
    purchase_orders,
    reports,
    sale_orders,
    stock_inventories,
    stock_moves,
    supplier_invoices,
    supplier_payments,
    users,
    warehouses,
)
from app.services.audit import register_audit_listeners
from app.services.seed import seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    register_audit_listeners()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title="TECHNOVA ERP - SEYAL-TCHAD", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(branches.router)
app.include_router(audit_logs.router)
app.include_router(product_catalog.router)
app.include_router(products.router)
app.include_router(partners.router)
app.include_router(purchase_orders.router)
app.include_router(containers.router)
app.include_router(imports.router)
app.include_router(warehouses.router)
app.include_router(stock_moves.router)
app.include_router(stock_inventories.router)
app.include_router(sale_orders.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(fleet.router)
app.include_router(deliveries.router)
app.include_router(supplier_invoices.router)
app.include_router(supplier_payments.router)
app.include_router(finance.router)
app.include_router(fleet_ops.router)
app.include_router(commercial.router)
app.include_router(hr.router)
app.include_router(reports.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
