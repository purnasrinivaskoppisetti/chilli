from datetime import date
from decimal import Decimal
import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    OWNER = "owner"
    STAFF = "staff"


class CropType(str, enum.Enum):
    MIRCHI = "mirchi"
    COTTON = "cotton"


class PaymentMode(str, enum.Enum):
    CASH = "cash"
    UPI = "upi"
    BANK = "bank"
    OTHER = "other"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True)
    email = Column(String(100), unique=True)
    password_hash = Column(Text, nullable=False)
    role = Column(Enum(UserRole, name="userrole"), nullable=False, default=UserRole.STAFF)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    purchases = relationship("Purchase", back_populates="created_by")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    mobile = Column(String(20), index=True)
    village = Column(String(100))
    address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    purchases = relationship("Purchase", back_populates="customer", cascade="all, delete-orphan")


class DeductionSlab(Base):
    __tablename__ = "deduction_slabs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crop = Column(Enum(CropType, name="croptype"), nullable=False)
    min_weight = Column(Numeric(10, 2), nullable=False)
    max_weight = Column(Numeric(10, 2), nullable=False)
    deduction_kg = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    crop = Column(Enum(CropType, name="croptype"), nullable=False)
    purchase_date = Column(Date, nullable=False, default=date.today)
    price_per_kg = Column(Numeric(10, 2), nullable=False)
    total_bags = Column(Integer, default=0, nullable=False)
    gross_weight = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total_deduction = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    net_weight = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    payment_status = Column(Enum(PaymentStatus, name="paymentstatus"), default=PaymentStatus.PENDING, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer = relationship("Customer", back_populates="purchases")
    created_by = relationship("User", back_populates="purchases")
    bags = relationship("PurchaseBag", back_populates="purchase", cascade="all, delete-orphan", order_by="PurchaseBag.bag_number")
    payments = relationship("Payment", back_populates="purchase", cascade="all, delete-orphan")

    def recalculate_totals(self):
        self.total_bags = len(self.bags)
        self.gross_weight = sum((b.gross_weight for b in self.bags), Decimal("0.00"))
        self.total_deduction = sum((b.deduction_kg for b in self.bags), Decimal("0.00"))
        self.net_weight = sum((b.net_weight for b in self.bags), Decimal("0.00"))
        self.total_amount = self.net_weight * self.price_per_kg


class PurchaseBag(Base):
    __tablename__ = "purchase_bags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    bag_number = Column(Integer, nullable=False)
    gross_weight = Column(Numeric(10, 2), nullable=False)
    deduction_kg = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    net_weight = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    purchase = relationship("Purchase", back_populates="bags")

    __table_args__ = (
        UniqueConstraint("purchase_id", "bag_number", name="uq_bag_per_purchase"),
    )

    def compute_net(self):
        self.net_weight = self.gross_weight - self.deduction_kg


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    amount_paid = Column(Numeric(12, 2), nullable=False)
    payment_mode = Column(Enum(PaymentMode, name="paymentmode"), nullable=False, default=PaymentMode.CASH)
    remarks = Column(Text)
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    purchase = relationship("Purchase", back_populates="payments")
