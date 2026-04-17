from datetime import date, timedelta
from sqlalchemy import select, func
from app.models.models import Purchase, CropType, PaymentStatus


class DashboardService:

    @staticmethod
    async def get_dashboard(db):

        today = date.today()
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

        # -----------------------------
        # 1. TODAY SUMMARY
        # -----------------------------
        today_result = await db.execute(
            select(
                func.count(Purchase.id),
                func.sum(Purchase.net_weight),
                func.sum(Purchase.total_amount)
            ).where(Purchase.purchase_date == today)
        )

        today_data = today_result.first()

        today_purchases = today_data[0] or 0
        today_weight = float(today_data[1] or 0)
        today_spent = float(today_data[2] or 0)

        # -----------------------------
        # 2. PENDING PAYMENTS
        # -----------------------------
        pending_result = await db.execute(
            select(func.count(Purchase.id)).where(
                Purchase.payment_status != PaymentStatus.PAID
            )
        )
        pending_count = pending_result.scalar() or 0

        # -----------------------------
        # 3. WEEKLY DATA (COTTON + MIRCHI)
        # -----------------------------
        weekly_data = []

        for day in last_7_days:
            result = await db.execute(
                select(
                    Purchase.crop,
                    func.sum(Purchase.net_weight)
                ).where(Purchase.purchase_date == day)
                .group_by(Purchase.crop)
            )

            data = {row[0]: float(row[1]) for row in result}

            weekly_data.append({
                "date": str(day),
                "cotton_kg": data.get(CropType.COTTON, 0),
                "mirchi_kg": data.get(CropType.MIRCHI, 0)
            })

        # -----------------------------
        # 4. RECENT TRANSACTIONS
        # -----------------------------
        recent_result = await db.execute(
            select(Purchase)
            .order_by(Purchase.created_at.desc())
            .limit(5)
        )

        recent = []
        for p in recent_result.scalars():
            recent.append({
                "customer_id": p.customer_id,
                "invoice": p.invoice_number,
                "amount": float(p.total_amount),
                "status": p.payment_status,
                "date": str(p.purchase_date)
            })

        # -----------------------------
        # FINAL RESPONSE
        # -----------------------------
        return {
            "success": True,
            "message": "Dashboard data fetched successfully",
            "data": {
                "today": {
                    "total_purchases": today_purchases,
                    "total_weight_kg": today_weight,
                    "total_spent": today_spent,
                    "pending_payments": pending_count
                },
                "weekly_trends": weekly_data,
                "recent_transactions": recent
            }
        }