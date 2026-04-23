from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import Payment, Refund, PaymentStatus, RefundStatus
from .schemas import PaymentCreate, RefundCreate
import asyncio
import random
import uuid

async def create_payment(db: AsyncSession, user_id: str, payload: PaymentCreate):
    db_payment = Payment(**payload.model_dump(), user_id=user_id)
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment

async def get_payment(db: AsyncSession, payment_id: str):
    result = await db.execute(select(Payment).filter(Payment.id == payment_id))
    return result.scalars().first()

async def get_payment_by_order(db: AsyncSession, order_id: str):
    result = await db.execute(select(Payment).filter(Payment.order_id == order_id))
    return result.scalars().first()

async def process_simulated_payment(db: AsyncSession, payment_id: str):
    # Simulate processing delay 1-2s
    await asyncio.sleep(random.uniform(1.0, 2.0))
    
    db_payment = await get_payment(db, payment_id)
    if not db_payment:
        return None
        
    # 10% failure rate
    if random.random() < 0.1:
        db_payment.status = PaymentStatus.FAILED
        db_payment.failure_reason = "Simulated bank decline"
    else:
        db_payment.status = PaymentStatus.SUCCESS
        db_payment.provider_reference = f"sim_{uuid.uuid4().hex[:8]}"
        
    await db.commit()
    await db.refresh(db_payment)
    return db_payment

async def create_refund(db: AsyncSession, payment_id: str, payload: RefundCreate):
    payment = await get_payment(db, payment_id)
    if not payment or payment.status != PaymentStatus.SUCCESS:
        return None
        
    db_refund = Refund(payment_id=payment_id, amount=payload.amount, reason=payload.reason)
    db.add(db_refund)
    await db.commit()
    
    # Process refund immediately
    db_refund.status = RefundStatus.PROCESSED
    await db.commit()
    await db.refresh(db_refund)
    return db_refund
