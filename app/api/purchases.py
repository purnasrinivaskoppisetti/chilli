from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.schemas.purchase import PurchaseCreateSchema
from app.services.purchase_service import PurchaseService
from app.api.deps import get_current_user
from app.models.models import Purchase, Customer

router = APIRouter()


@router.post("/preview")
async def preview_purchase(
    payload: PurchaseCreateSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    data = await PurchaseService.calculate_preview(payload)

    return {
        "success": True,
        "message": "Preview calculated successfully",
        "data": data
    }


@router.post("/create")
async def create_purchase(
    payload: PurchaseCreateSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    result = await PurchaseService.create_purchase(payload, db, user.id)

    return {
        "success": True,
        "message": "Purchase saved successfully",
        "data": result
    }



# -----------------------------
# HISTORY + SEARCH
# -----------------------------
@router.get("/")
async def get_purchases(
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    query = (
        select(Purchase)
        .options(selectinload(Purchase.customer), selectinload(Purchase.payments))
        .order_by(desc(Purchase.created_at))
    )

    if search:
        query = query.join(Customer).where(
            or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.mobile.ilike(f"%{search}%")
            )
        )

    result = await db.execute(query)
    purchases = result.scalars().all()

    data = []

    for p in purchases:
        total_paid = sum([float(x.amount_paid) for x in p.payments])
        pending = float(p.total_amount) - total_paid

        data.append({
            "id": p.id,
            "customer": p.customer.name,
            "mobile": p.customer.mobile,
            "crop": p.crop.value,
            "date": str(p.purchase_date),
            "bags": p.total_bags,
            "net_weight": float(p.net_weight),
            "total": float(p.total_amount),
            "paid": total_paid,
            "pending": pending,
            "status": p.payment_status.value
        })

    return {"success": True, "data": data}


# -----------------------------
# DELETE
# -----------------------------
@router.delete("/{id}")
async def delete_purchase(
    id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    result = await db.execute(select(Purchase).where(Purchase.id == id))
    purchase = result.scalar_one_or_none()

    if not purchase:
        return {"success": False, "message": "Not found"}

    await db.delete(purchase)
    await db.commit()

    return {"success": True, "message": "Deleted successfully"}



@router.get("/")
async def get_purchases(
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    query = (
        select(Purchase)
        .options(
            selectinload(Purchase.customer),
            selectinload(Purchase.payments)
        )
        .order_by(desc(Purchase.created_at))
    )

    if search:
        query = query.join(Customer).where(
            or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.mobile.ilike(f"%{search}%")
            )
        )

    result = await db.execute(query)
    purchases = result.scalars().all()

    data = []

    for p in purchases:
        total_paid = sum([float(pay.amount_paid) for pay in p.payments])
        pending = float(p.total_amount) - total_paid

        data.append({
            "purchase_id": p.id,
            "customer_name": p.customer.name,
            "mobile": p.customer.mobile,
            "crop": p.crop.value,
            "date": str(p.purchase_date),
            "bags": p.total_bags,
            "net_weight": float(p.net_weight),
            "total_amount": float(p.total_amount),
            "paid": total_paid,
            "pending": pending,
            "status": p.payment_status.value
        })

    return {
        "success": True,
        "data": data
    }


@router.get("/{purchase_id}")
async def get_purchase_invoice(
    purchase_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    result = await db.execute(
        select(Purchase)
        .where(Purchase.id == purchase_id)
        .options(
            selectinload(Purchase.customer),
            selectinload(Purchase.bags),
            selectinload(Purchase.payments)
        )
    )

    purchase = result.scalar_one_or_none()

    if not purchase:
        return {"success": False, "message": "Purchase not found"}

    # -------------------------
    # BAGS
    # -------------------------
    bags_data = []
    for bag in purchase.bags:
        bags_data.append({
            "bag_number": bag.bag_number,
            "gross_weight": float(bag.gross_weight),
            "deduction": float(bag.deduction_kg),
            "net_weight": float(bag.net_weight)
        })

    # -------------------------
    # PAYMENTS
    # -------------------------
    payments_data = []
    total_paid = 0

    for pay in purchase.payments:
        total_paid += float(pay.amount_paid)

        payments_data.append({
            "amount": float(pay.amount_paid),
            "mode": pay.payment_mode.value,
            "remarks": pay.remarks,
            "date": str(pay.payment_date)
        })

    pending = float(purchase.total_amount) - total_paid

    # -------------------------
    # FINAL RESPONSE
    # -------------------------
    return {
        "success": True,
        "data": {
            "invoice_number": purchase.invoice_number,
            "date": str(purchase.purchase_date),

            "customer": {
                "name": purchase.customer.name,
                "mobile": purchase.customer.mobile
            },

            "crop": purchase.crop.value,
            "price_per_kg": float(purchase.price_per_kg),

            "bags": bags_data,

            "totals": {
                "total_bags": purchase.total_bags,
                "gross_weight": float(purchase.gross_weight),
                "total_deduction": float(purchase.total_deduction),
                "net_weight": float(purchase.net_weight),
                "total_amount": float(purchase.total_amount)
            },

            "payment": {
                "paid": total_paid,
                "pending": pending,
                "status": purchase.payment_status.value,
                "history": payments_data
            },

            "notes": purchase.notes
        }
    }