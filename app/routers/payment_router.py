from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_user_headers
from app.schemas import StandardResponse, PaymentResponse, PaymentCreate, RefundCreate, RefundResponse
from app.services import payment_service
from app.events.publisher import publish_event
from app.models.models import PaymentStatus

router = APIRouter(prefix="/payments", tags=["Payments"])

def format_response(data, message="Success"):
    return {"data": data, "message": message, "status": "success"}

async def async_process_payment(payment_id: str, db: AsyncSession):
    payment = await payment_service.process_simulated_payment(db, payment_id)
    if payment:
        if payment.status == PaymentStatus.SUCCESS:
            await publish_event("payment.success", {
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
                "user_id": str(payment.user_id),
                "amount": float(payment.amount),
                "user_email": payment.user_email,
                "user_name": payment.user_name,
                "restaurant_name": payment.restaurant_name,
                "items": payment.items,
                "delivery_floor": payment.delivery_floor,
                "delivery_wing": payment.delivery_wing,
                "estimated_minutes": payment.estimated_minutes
            })
        elif payment.status == PaymentStatus.FAILED:
            await publish_event("payment.failed", {
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
                "user_id": str(payment.user_id),
                "amount": float(payment.amount),
                "user_email": payment.user_email,
                "user_name": payment.user_name,
                "reason": payment.failure_reason
            })

@router.post("", response_model=StandardResponse)
async def init_payment(payload: PaymentCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), headers: dict = Depends(get_user_headers)):
    user_id = headers.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user_id header")
    
    payment = await payment_service.create_payment(db, user_id, payload)
    # Background simulate processing
    background_tasks.add_task(async_process_payment, str(payment.id), db)
    
    return format_response(PaymentResponse.model_validate(payment).model_dump(mode="json"), "Payment initiated")

@router.get("/{id}", response_model=StandardResponse)
async def get_payment(id: str, db: AsyncSession = Depends(get_db)):
    payment = await payment_service.get_payment(db, id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return format_response(PaymentResponse.model_validate(payment).model_dump(mode="json"))

@router.get("/order/{order_id}", response_model=StandardResponse)
async def get_payment_for_order(order_id: str, db: AsyncSession = Depends(get_db)):
    payment = await payment_service.get_payment_by_order(db, order_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return format_response(PaymentResponse.model_validate(payment).model_dump(mode="json"))

@router.post("/{id}/refund", response_model=StandardResponse)
async def refund_payment(id: str, payload: RefundCreate, db: AsyncSession = Depends(get_db)):
    refund = await payment_service.create_refund(db, id, payload)
    if not refund:
        raise HTTPException(status_code=400, detail="Cannot refund this payment")
        
    await publish_event("refund.processed", {
        "refund_id": str(refund.id),
        "payment_id": str(refund.payment_id),
        "order_id": str((await payment_service.get_payment(db, id)).order_id)
    })
    
    return format_response(RefundResponse.model_validate(refund).model_dump(mode="json"), "Refund processed")
