from pydantic import BaseModel
from typing import List, Optional
import enum
from datetime import date


class CropType(str, enum.Enum):
    MIRCHI = "mirchi"
    COTTON = "cotton"


class BagSchema(BaseModel):
    bag_number: int
    gross_weight: float
    deduction: float


class PaymentSchema(BaseModel):
    amount_paid: float = 0
    payment_mode: str = "cash"
    remarks: Optional[str] = None


class PurchaseCreateSchema(BaseModel):
    customer_name: str
    mobile: str
    crop: CropType
    type: Optional[str] = None   # ✅ dynamic field
    price_per_kg: float
    purchase_date: date
    bags: List[BagSchema]
    payment: Optional[PaymentSchema] = None
    notes: Optional[str] = None