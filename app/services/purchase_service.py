from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.models import (
    Purchase,
    PurchaseBag,
    Customer,
    Payment,
    PaymentStatus
)


class PurchaseService:

    # --------------------------------
    # ₹40 DEDUCTION PER BAG
    # --------------------------------
    BAG_DEDUCTION = Decimal("40")

    # -----------------------------
    # PREVIEW (FAST)
    # -----------------------------
    @staticmethod
    async def calculate_preview(payload):

        total_gross = Decimal("0")
        total_deduction = Decimal("0")
        total_net = Decimal("0")

        bags_preview = []

        for bag in payload.bags:

            gross = Decimal(bag.gross_weight)
            deduction = Decimal(bag.deduction)

            if deduction > gross:
                raise ValueError(
                    f"Invalid deduction for bag {bag.bag_number}"
                )

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

        # -----------------------------
        # TOTAL CALCULATION
        # -----------------------------
        total_bags = len(payload.bags)

        total_amount = (
            total_net * Decimal(payload.price_per_kg)
        )

        # ₹40 deduction per bag
        bag_charge = (
            Decimal(total_bags) *
            PurchaseService.BAG_DEDUCTION
        )

        final_amount = total_amount - bag_charge

        # PAYMENT
        paid_amount = (
            Decimal(payload.payment.amount_paid)
            if payload.payment
            else Decimal("0")
        )

        pending_amount = final_amount - paid_amount

        return {

            # 🔹 CUSTOMER INFO
            "customer": {
                "name": payload.customer_name,
                "mobile": payload.mobile
            },

            # 🔹 PURCHASE INFO
            "purchase": {
                "crop": payload.crop,
                "type": payload.type,
                "price_per_kg": float(payload.price_per_kg),
                "date": str(payload.purchase_date),
                "notes": payload.notes
            },

            # 🔹 BAG DETAILS
            "bags": bags_preview,

            # 🔹 TOTALS
            "totals": {
                "total_bags": total_bags,
                "gross_weight": float(total_gross),
                "total_deduction": float(total_deduction),
                "net_weight": float(total_net),
                "price_per_kg": float(payload.price_per_kg),

                # NEW
                "bag_charge": float(bag_charge),

                "total_amount_before_deduction": float(total_amount),

                "final_amount": float(final_amount)
            },

            # 🔹 PAYMENT PREVIEW
            "payment": {
                "paid_amount": float(paid_amount),
                "pending_amount": float(pending_amount),
                "mode": (
                    payload.payment.payment_mode
                    if payload.payment
                    else None
                )
            }
        }

    # -----------------------------
    # CREATE PURCHASE (OPTIMIZED)
    # -----------------------------
    @staticmethod
    async def create_purchase(payload, db, user_id):

        # -----------------------------
        # CUSTOMER
        # -----------------------------
        result = await db.execute(
            select(Customer).where(
                Customer.mobile == payload.mobile
            )
        )

        customer = result.scalar_one_or_none()

        if not customer:
            customer = Customer(
                name=payload.customer_name,
                mobile=payload.mobile
            )

            db.add(customer)
            await db.flush()

        # -----------------------------
        # PURCHASE
        # -----------------------------
        purchase = Purchase(
            customer_id=customer.id,
            user_id=user_id,
            crop=payload.crop,
            type=payload.type,
            price_per_kg=payload.price_per_kg,
            purchase_date=payload.purchase_date,
            notes=payload.notes
        )

        db.add(purchase)
        await db.flush()

        # -----------------------------
        # CALCULATIONS
        # -----------------------------
        total_bags = 0
        total_gross = Decimal("0")
        total_deduction = Decimal("0")
        total_net = Decimal("0")

        for bag in payload.bags:

            gross = Decimal(bag.gross_weight)
            deduction = Decimal(bag.deduction)

            if deduction > gross:
                raise ValueError(
                    f"Invalid deduction for bag {bag.bag_number}"
                )

            net = gross - deduction

            total_bags += 1
            total_gross += gross
            total_deduction += deduction
            total_net += net

            db.add(
                PurchaseBag(
                    purchase_id=purchase.id,
                    bag_number=bag.bag_number,
                    gross_weight=gross,
                    deduction_kg=deduction,
                    net_weight=net
                )
            )

        # -----------------------------
        # TOTALS
        # -----------------------------
        purchase.total_bags = total_bags
        purchase.gross_weight = total_gross
        purchase.total_deduction = total_deduction
        purchase.net_weight = total_net

        # BEFORE BAG DEDUCTION
        raw_total_amount = (
            total_net *
            Decimal(payload.price_per_kg)
        )

        # ₹40 deduction per bag
        bag_charge = (
            Decimal(total_bags) *
            PurchaseService.BAG_DEDUCTION
        )

        # FINAL TOTAL
        final_total_amount = (
            raw_total_amount - bag_charge
        )

        purchase.total_amount = final_total_amount

        total_amount = final_total_amount

        # -----------------------------
        # PAYMENT
        # -----------------------------
        paid_amount = Decimal("0")

        if (
            payload.payment and
            payload.payment.amount_paid > 0
        ):

            paid_amount = Decimal(
                payload.payment.amount_paid
            )

            db.add(
                Payment(
                    purchase_id=purchase.id,
                    amount_paid=paid_amount,
                    payment_mode=payload.payment.payment_mode,
                    remarks=payload.payment.remarks
                )
            )

        # -----------------------------
        # PAYMENT STATUS
        # -----------------------------
        if paid_amount == 0:
            purchase.payment_status = (
                PaymentStatus.PENDING
            )

        elif paid_amount < total_amount:
            purchase.payment_status = (
                PaymentStatus.PARTIAL
            )

        else:
            purchase.payment_status = (
                PaymentStatus.PAID
            )

        # -----------------------------
        # INVOICE NUMBER
        # -----------------------------
        purchase.invoice_number = (
            f"INV-{purchase.purchase_date.year}-{purchase.id:05d}"
        )

        await db.commit()
        await db.refresh(purchase)

        return {
            "invoice_number": purchase.invoice_number,

            "type": purchase.type,

            "total_bags": total_bags,

            "gross_weight": float(total_gross),

            "total_deduction_weight": float(total_deduction),

            "net_weight": float(total_net),

            "price_per_kg": float(payload.price_per_kg),

            "total_amount_before_deduction": float(
                raw_total_amount
            ),

            # NEW
            "bag_charge": float(bag_charge),

            "final_total_amount": float(total_amount),

            "paid_amount": float(paid_amount),

            "pending_amount": float(
                total_amount - paid_amount
            ),

            "status": purchase.payment_status.value
        }

    # -----------------------------
    # ADD PAYMENT
    # -----------------------------
    @staticmethod
    async def add_payment(purchase_id, payload, db):

        result = await db.execute(
            select(Purchase)
            .where(Purchase.id == purchase_id)
            .options(
                selectinload(Purchase.payments)
            )
        )

        purchase = result.scalar_one_or_none()

        if not purchase:
            raise ValueError("Purchase not found")

        # -------------------------
        # ADD PAYMENT
        # -------------------------
        new_payment = Payment(
            purchase_id=purchase.id,
            amount_paid=Decimal(payload.amount_paid),
            payment_mode=payload.payment_mode,
            remarks=payload.remarks
        )

        db.add(new_payment)
        await db.flush()

        # -------------------------
        # RECALCULATE TOTAL
        # -------------------------
        total_paid = (
            sum([
                p.amount_paid
                for p in purchase.payments
            ]) +
            Decimal(payload.amount_paid)
        )

        total_amount = purchase.total_amount

        pending_amount = (
            total_amount - total_paid
        )

        # -------------------------
        # STATUS
        # -------------------------
        if total_paid == 0:

            purchase.payment_status = (
                PaymentStatus.PENDING
            )

        elif total_paid < total_amount:

            purchase.payment_status = (
                PaymentStatus.PARTIAL
            )

        else:

            purchase.payment_status = (
                PaymentStatus.PAID
            )

        await db.commit()
        await db.refresh(purchase)

        return {
            "purchase_id": purchase.id,

            "total_amount": float(total_amount),

            "paid_amount": float(total_paid),

            "pending_amount": float(pending_amount),

            "status": purchase.payment_status.value
        }