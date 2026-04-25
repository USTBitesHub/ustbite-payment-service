from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Payment, Refund, PaymentStatus, PaymentMethod, RefundStatus
from app.schemas import PaymentCreate, RefundCreate
from app.config import settings
import asyncio
import hmac
import hashlib
import uuid

async def _create_razorpay_order(amount_decimal, receipt: str) -> dict:
    """Run the synchronous Razorpay SDK call in a thread pool."""
    import razorpay
    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    amount_paise = int(float(amount_decimal) * 100)
    return await asyncio.to_thread(
        client.order.create,
        {"amount": amount_paise, "currency": "INR", "receipt": receipt}
    )

async def create_payment(db: AsyncSession, user_id: str, payload: PaymentCreate):
    razorpay_order_id = None

    if payload.method == PaymentMethod.CASH_ON_DELIVERY:
        # COD payments are confirmed immediately — no payment gateway needed
        db_payment = Payment(**payload.model_dump(), user_id=user_id)
        db.add(db_payment)
        await db.commit()
        await db.refresh(db_payment)
        db_payment.status = PaymentStatus.SUCCESS
        db_payment.provider_reference = "COD"
        await db.commit()
        await db.refresh(db_payment)
        return db_payment

    # UPI / CARD — create a Razorpay order if keys are configured
    if settings.razorpay_key_id and settings.razorpay_key_secret:
        try:
            rp_order = await _create_razorpay_order(payload.amount, str(payload.order_id))
            razorpay_order_id = rp_order.get("id")
        except Exception as e:
            print(f"[warn] Razorpay order creation failed (falling back to pending): {e}")

    db_payment = Payment(**payload.model_dump(), user_id=user_id, razorpay_order_id=razorpay_order_id)
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

async def verify_razorpay_payment(
    db: AsyncSession,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> Payment | None:
    """Verify Razorpay signature and mark payment as SUCCESS."""
    msg = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_sig = hmac.new(
        settings.razorpay_key_secret.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if expected_sig != razorpay_signature:
        return None

    result = await db.execute(
        select(Payment).filter(Payment.razorpay_order_id == razorpay_order_id)
    )
    db_payment = result.scalars().first()
    if not db_payment:
        return None

    db_payment.status = PaymentStatus.SUCCESS
    db_payment.provider_reference = razorpay_payment_id
    await db.commit()
    await db.refresh(db_payment)
    return db_payment

async def process_simulated_payment(db: AsyncSession, payment_id: str):
    """Legacy simulator kept for backwards-compat (not called in normal flow)."""
    await asyncio.sleep(0)
    db_payment = await get_payment(db, payment_id)
    if not db_payment:
        return None
    if db_payment.status == PaymentStatus.PENDING:
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

    db_refund.status = RefundStatus.PROCESSED
    await db.commit()
    await db.refresh(db_refund)
    return db_refund
