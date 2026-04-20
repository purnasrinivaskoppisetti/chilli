# app/schemas/payment.py

from pydantic import BaseModel
from typing import Optional

class PaymentCreateSchema(BaseModel):
    amount_paid: float
    payment_mode: str = "cash"
    remarks: Optional[str] = None