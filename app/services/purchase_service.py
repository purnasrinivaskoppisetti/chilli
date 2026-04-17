from decimal import Decimal
from sqlalchemy import select
from app.models.models import Purchase, PurchaseBag, Customer, Payment, PaymentStatus


class PurchaseService:

    # -----------------------------
    # PREVIEW
    # -----------------------------
    @staticmethod
    async def calculate_preview(payload):

        total_gross = Decimal("0")
        total_deduction = Decimal("0")
        total_net = Decimal("0")

        bags_preview = []

        for bag in payload.bags:

            if bag.deduction > bag.gross_weight:
                raise ValueError(f"Deduction cannot exceed weight for bag {bag.bag_number}")

            if bag.gross_weight < 0 or bag.deduction < 0:
                raise ValueError("Invalid weight/deduction")

            gross = Decimal(bag.gross_weight)
            deduction = Decimal(bag.deduction)
            net = gross - deduction

            total_gross += gross
            total_deduction += deduction
            total_net += net

            bags_preview.append({
                "bag_number": bag.bag_number,
                "gross_weight": float(gross),
                "deduction": float(deduction),
                "net_weight": float(net)
            })

        total_amount = total_net * Decimal(payload.price_per_kg)

        return {
            "bags": bags_preview,
            "totals": {
                "total_bags": len(payload.bags),
                "gross": float(total_gross),
                "deduction": float(total_deduction),
                "net": float(total_net),
                "price_per_kg": float(payload.price_per_kg),
                "amount": float(total_amount)
            }
        }

    # -----------------------------
    # CREATE PURCHASE
    # -----------------------------
    @staticmethod
    async def create_purchase(payload, db, user_id):

        # -------------------------
        # 1. Customer
        # -------------------------
        result = await db.execute(
            select(Customer).where(Customer.mobile == payload.mobile)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            customer = Customer(
                name=payload.customer_name,
                mobile=payload.mobile
            )
            db.add(customer)
            await db.flush()

        # -------------------------
        # 2. Purchase
        # -------------------------
        purchase = Purchase(
            customer_id=customer.id,
            user_id=user_id,
            crop=payload.crop,
            price_per_kg=payload.price_per_kg,
            purchase_date=payload.purchase_date,
            notes=payload.notes
        )

        db.add(purchase)
        await db.flush()

        # -------------------------
        # 3. Bags + CALCULATE TOTALS (IMPORTANT FIX)
        # -------------------------
        total_bags = 0
        total_gross = Decimal("0")
        total_deduction = Decimal("0")
        total_net = Decimal("0")

        for bag in payload.bags:

            gross = Decimal(bag.gross_weight)
            deduction = Decimal(bag.deduction)

            if deduction > gross:
                raise ValueError(f"Invalid deduction for bag {bag.bag_number}")

            net = gross - deduction

            total_bags += 1
            total_gross += gross
            total_deduction += deduction
            total_net += net

            db.add(PurchaseBag(
                purchase_id=purchase.id,
                bag_number=bag.bag_number,
                gross_weight=gross,
                deduction_kg=deduction,
                net_weight=net
            ))

        await db.flush()

        # -------------------------
        # 4. SET TOTALS (NO recalculate_totals)
        # -------------------------
        purchase.total_bags = total_bags
        purchase.gross_weight = total_gross
        purchase.total_deduction = total_deduction
        purchase.net_weight = total_net
        purchase.total_amount = total_net * Decimal(payload.price_per_kg)

        total_amount = purchase.total_amount
        paid_amount = Decimal("0")

        # -------------------------
        # 5. PAYMENT
        # -------------------------
        if payload.payment and payload.payment.amount_paid > 0:

            paid_amount = Decimal(payload.payment.amount_paid)

            db.add(Payment(
                purchase_id=purchase.id,
                amount_paid=paid_amount,
                payment_mode=payload.payment.payment_mode,
                remarks=payload.payment.remarks
            ))

        # -------------------------
        # 6. STATUS
        # -------------------------
        if paid_amount == 0:
            purchase.payment_status = PaymentStatus.PENDING
        elif paid_amount < total_amount:
            purchase.payment_status = PaymentStatus.PARTIAL
        else:
            purchase.payment_status = PaymentStatus.PAID

        # -------------------------
        # 7. INVOICE
        # -------------------------
        purchase.invoice_number = f"INV-{purchase.purchase_date.year}-{purchase.id:05d}"

        await db.commit()
        await db.refresh(purchase)

        # -------------------------
        # 8. RESPONSE
        # -------------------------
        return {
            "invoice_number": purchase.invoice_number,
            "total_amount": float(total_amount),
            "paid_amount": float(paid_amount),
            "pending_amount": float(total_amount - paid_amount),
            "status": purchase.payment_status.value
        }