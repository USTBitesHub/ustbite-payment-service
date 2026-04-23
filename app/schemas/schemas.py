from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from .models import PaymentStatus, PaymentMethod, RefundStatus

class StandardResponse(BaseModel):
    data: Optional[dict] = None
    message: str
    status: str

class PaymentCreate(BaseModel):
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    restaurant_name: Optional[str] = None
    delivery_floor: Optional[str] = None
    delivery_wing: Optional[str] = None
    estimated_minutes: Optional[int] = None
    items: Optional[list] = None
    order_id: UUID
    amount: Decimal
    method: PaymentMethod

class RefundCreate(BaseModel):
    amount: Decimal
    reason: Optional[str] = None

class PaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    method: PaymentMethod
    provider_reference: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RefundResponse(BaseModel):
    id: UUID
    payment_id: UUID
    amount: Decimal
    reason: Optional[str]
    status: RefundStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
