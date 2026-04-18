from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import Customer, Purchase, Payment

router = APIRouter()


@router.get("/")
async def get_customers(
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    # Base query
    query = select(Customer)

    if search:
        query = query.where(
            or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.mobile.ilike(f"%{search}%")
            )
        )

    result = await db.execute(query)
    customers = result.scalars().all()

    response = []

    for customer in customers:

        # Get purchases
        purchase_result = await db.execute(
            select(Purchase)
            .where(Purchase.customer_id == customer.id)
            .options(selectinload(Purchase.payments))
        )

        purchases = purchase_result.scalars().all()

        total_orders = len(purchases)
        total_amount = 0
        total_paid = 0

        for p in purchases:
            total_amount += float(p.total_amount)

            for pay in p.payments:
                total_paid += float(pay.amount_paid)

        pending = total_amount - total_paid

        response.append({
            "customer_id": customer.id,
            "name": customer.name,
            "mobile": customer.mobile,
            "total_orders": total_orders,
            "total_amount": total_amount,
            "pending_amount": pending
        })

    return {
        "success": True,
        "data": response
    }