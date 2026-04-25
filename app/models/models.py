import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import enum
from sqlalchemy import Integer

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class PaymentMethod(str, enum.Enum):
    UPI = "UPI"
    CARD = "CARD"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"

class RefundStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    REJECTED = "REJECTED"

class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="INR")
    status = Column(Enum(PaymentStatus, name='payment_status'), default=PaymentStatus.PENDING)
    method = Column(Enum(PaymentMethod, name='payment_method'), nullable=False)
    provider_reference = Column(String)
    failure_reason = Column(String)
    razorpay_order_id = Column(String)
    user_email = Column(String)
    user_name = Column(String)
    restaurant_name = Column(String)
    delivery_floor = Column(String)
    delivery_wing = Column(String)
    estimated_minutes = Column(Integer)
    items = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Refund(Base):
    __tablename__ = "refunds"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String)
    status = Column(Enum(RefundStatus, name='refund_status'), default=RefundStatus.PENDING)
    user_email = Column(String)
    user_name = Column(String)
    restaurant_name = Column(String)
    delivery_floor = Column(String)
    delivery_wing = Column(String)
    estimated_minutes = Column(Integer)
    items = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
