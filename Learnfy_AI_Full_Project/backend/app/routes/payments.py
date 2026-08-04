"""Secure Stripe checkout, webhook, account, and admin routes."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.config.database import get_db
from app.config.settings import settings
from app.models.payment import Payment, Subscription
from app.models.user import User
from app.schemas.payment_schema import (
    AdminPaymentOut, CheckoutRequest, CheckoutResponse, MyPaymentsOut, PaymentOut,
    PaymentStatusOut, PlanOut, SubscriptionOut,
)
from app.services.stripe_service import (
    PLANS, amount_in_smallest_unit, configure_stripe,
    validate_checkout_configuration, validate_webhook_configuration,
)
from app.utils.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/payments", tags=["Payments"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def current_subscription(db: Session, user_id: int) -> Subscription | None:
    now = utcnow()
    candidates = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.current_period_end.desc()).all()
    )
    return next((item for item in candidates if as_utc(item.current_period_end) > now), None)


def activate_payment(db: Session, payment: Payment, provider_payment_id: str | None, method: str | None) -> str:
    if payment.status == "success":
        return "already_processed"
    plan = PLANS[payment.plan_code]
    now = utcnow()
    existing = current_subscription(db, payment.user_id)
    period_base = max(as_utc(existing.current_period_end), now) if existing else now
    payment.status = "success"
    payment.provider_payment_id = provider_payment_id or payment.provider_payment_id
    payment.payment_method = (method or "card")[:50]
    payment.status_message = "Payment completed"
    payment.paid_at = payment.paid_at or now
    if payment.subscription is None:
        db.add(Subscription(
            user_id=payment.user_id, plan_code=payment.plan_code, status="active",
            current_period_start=now,
            current_period_end=period_base + timedelta(days=plan.duration_days),
            source_payment_id=payment.id,
        ))
    return "success"


@router.get("/plans", response_model=list[PlanOut])
def list_plans():
    return [PlanOut(
        code=plan.code, name=plan.name, amount=plan.amount, currency="LKR",
        duration_days=plan.duration_days, features=list(plan.features),
    ) for plan in PLANS.values()]


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def create_checkout(payload: CheckoutRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = current_user.academic_profile
    if profile and profile.grade and profile.grade.grade_number and profile.grade.grade_number <= 13 and not profile.guardian_consent:
        raise HTTPException(status_code=403, detail="Parent or guardian confirmation is required for school-student payments")
    validate_checkout_configuration()
    configure_stripe()
    plan = PLANS[payload.plan_code]
    order_id = f"LFY-{utcnow():%Y%m%d%H%M%S}-{current_user.id}-{uuid4().hex[:10].upper()}"
    payment = Payment(
        user_id=current_user.id, order_id=order_id, provider="stripe", plan_code=plan.code,
        amount=plan.amount, currency="LKR", status="initiated",
    )
    db.add(payment)
    db.commit()
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=current_user.email,
            client_reference_id=order_id,
            metadata={"order_id": order_id, "user_id": str(current_user.id), "plan_code": plan.code},
            line_items=[{"price_data": {
                "currency": "lkr", "unit_amount": amount_in_smallest_unit(plan.amount),
                "product_data": {"name": plan.name},
            }, "quantity": 1}],
            phone_number_collection={"enabled": True},
            billing_address_collection="required",
            success_url=f"{frontend_url}/payments/result?order_id={order_id}",
            cancel_url=f"{frontend_url}/payments/result?order_id={order_id}&cancelled=1",
        )
    except stripe.StripeError as exc:
        payment.status = "failed"
        payment.status_message = str(exc.user_message or "Unable to create Stripe checkout")[:255]
        db.commit()
        raise HTTPException(status_code=502, detail="Unable to start Stripe checkout") from exc
    payment.provider_payment_id = session.id
    db.commit()
    return CheckoutResponse(order_id=order_id, checkout_url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    validate_webhook_configuration()
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook") from exc

    event_type = event["type"]
    obj = event["data"]["object"]
    if event_type not in {
        "checkout.session.completed", "checkout.session.async_payment_succeeded",
        "checkout.session.async_payment_failed", "checkout.session.expired",
    }:
        return {"status": "ignored"}
    order_id = obj.get("client_reference_id") or obj.get("metadata", {}).get("order_id")
    payment = db.query(Payment).filter(Payment.order_id == order_id, Payment.provider == "stripe").with_for_update().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment order not found")
    if obj.get("amount_total") != amount_in_smallest_unit(payment.amount) or obj.get("currency", "").upper() != payment.currency:
        raise HTTPException(status_code=400, detail="Payment amount or currency mismatch")

    if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"} and obj.get("payment_status") == "paid":
        result = activate_payment(db, payment, obj.get("payment_intent") or obj.get("id"), (obj.get("payment_method_types") or ["card"])[0])
    elif event_type == "checkout.session.completed":
        payment.status, payment.status_message, result = "pending", "Stripe payment is processing", "pending"
    elif event_type == "checkout.session.async_payment_failed":
        payment.status, payment.status_message, result = "failed", "Stripe payment failed", "failed"
    else:
        payment.status, payment.status_message, result = "cancelled", "Stripe checkout expired", "cancelled"
    db.commit()
    return {"status": result}


@router.get("/me", response_model=MyPaymentsOut)
def my_payments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    subscription = current_subscription(db, current_user.id)
    payments = db.query(Payment).filter(Payment.user_id == current_user.id).order_by(Payment.created_at.desc()).limit(20).all()
    return MyPaymentsOut(plan_code=subscription.plan_code if subscription else "free", is_premium=subscription is not None,
        subscription=SubscriptionOut.model_validate(subscription) if subscription else None,
        payments=[PaymentOut.model_validate(item) for item in payments])


@router.get("/status/{order_id}", response_model=PaymentStatusOut)
def payment_status(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    payment = db.query(Payment).filter(Payment.order_id == order_id, Payment.user_id == current_user.id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment order not found")
    return PaymentStatusOut(payment=PaymentOut.model_validate(payment),
        subscription=SubscriptionOut.model_validate(payment.subscription) if payment.subscription else None)


@router.get("/admin/transactions", response_model=list[AdminPaymentOut])
def admin_transactions(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    payments = db.query(Payment).options(joinedload(Payment.user)).order_by(Payment.created_at.desc()).limit(500).all()
    return [AdminPaymentOut(**PaymentOut.model_validate(payment).model_dump(), user_id=payment.user_id,
        user_name=payment.user.name, user_email=payment.user.email,
        subscription_expires_at=payment.subscription.current_period_end if payment.subscription else None) for payment in payments]
