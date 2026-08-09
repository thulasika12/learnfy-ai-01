"""Secure Stripe checkout, webhook, account, and admin routes."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import logging
from uuid import uuid4

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.config.database import get_db
from app.config.settings import settings
from app.models.payment import Payment, Subscription
from app.models.entitlement import StripeEvent
from app.models.user import User
from app.schemas.payment_schema import (
    AdminPaymentOut, CheckoutRequest, CheckoutResponse, MyPaymentsOut, PaymentOut,
    PayHereOrderRequest, PayHereOrderResponse,
    PaymentStatusOut, PlanOut, SubscriptionOut,
)
from app.services.stripe_service import (
    PLANS, configure_stripe, price_id_for,
    validate_checkout_configuration, validate_webhook_configuration,
)
from app.services.payhere_service import (
    amount_text, checkout_hash as payhere_checkout_hash, checkout_url as payhere_checkout_url,
    configuration as payhere_configuration, plans as payhere_plans,
    require_configuration as require_payhere_configuration, valid_notification_signature,
)
from app.services.rate_limit import enforce
from app.utils.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/payments", tags=["Payments"])
logger = logging.getLogger("learnfy.payments")


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


@router.get("/plans", response_model=list[PlanOut])
def list_plans():
    if settings.PAYMENT_PROVIDER == "payhere":
        free = PlanOut(code="free", name="Free", amount=Decimal("0.00"), currency="LKR",
                       duration_days=None, features=["Notes and community", "Basic learning tools"])
        paid = [PlanOut(code=plan.code, name=plan.name, amount=plan.amount, currency="LKR",
                        duration_days=plan.duration_days, features=list(plan.features))
                for plan in payhere_plans().values()]
        return [free, *paid]
    return [PlanOut(
        code=plan.code, name=plan.name, amount=plan.amount, currency="LKR",
        duration_days=plan.duration_days, features=list(plan.features),
    ) for plan in PLANS.values()]

@router.get("/config")
@router.get("/configuration", include_in_schema=False)
def payment_configuration():
    if settings.PAYMENT_PROVIDER == "payhere":
        configured, message = payhere_configuration()
        return {"enabled":configured, "provider":"payhere" if configured else None,
                "sandbox":settings.PAYHERE_SANDBOX, "message":message}
    configured = bool(settings.PAYMENTS_ENABLED and settings.PAYMENT_PROVIDER == "stripe" and
                      settings.STRIPE_SECRET_KEY and settings.STRIPE_MONTHLY_PRICE_ID and settings.STRIPE_YEARLY_PRICE_ID)
    return {"enabled": configured, "provider": settings.PAYMENT_PROVIDER if configured else None,
            "message": None if configured else "Payments are currently unavailable"}

@router.post("/payhere/create-order", response_model=PayHereOrderResponse, status_code=201)
def create_payhere_order(payload: PayHereOrderRequest, request: Request,
                         db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enforce(request, "payhere_create_order", 5, 300, current_user.id)
    require_payhere_configuration()
    plan = payhere_plans()[payload.plan_code]
    order_id = f"LFY-PH-{uuid4().hex.upper()}"
    payment = Payment(user_id=current_user.id, order_id=order_id, provider="payhere",
                      plan_code=plan.code, amount=plan.amount, currency="LKR", status="initiated")
    db.add(payment); db.commit()
    frontend = settings.FRONTEND_URL.rstrip("/")
    backend = settings.BACKEND_PUBLIC_URL.rstrip("/")
    name_parts = current_user.name.strip().split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else "-"
    fields = {
        "merchant_id":settings.PAYHERE_MERCHANT_ID,
        "return_url":f"{frontend}/payments/result?order_id={order_id}",
        "cancel_url":f"{frontend}/payments/result?order_id={order_id}&cancelled=1",
        "notify_url":f"{backend}/payments/payhere/notify",
        "first_name":first_name, "last_name":last_name, "email":current_user.email,
        "phone":payload.phone.strip(), "address":payload.address.strip(), "city":payload.city.strip(),
        "country":"Sri Lanka", "order_id":order_id, "items":plan.name,
        "currency":"LKR", "amount":amount_text(plan.amount),
        "custom_1":str(current_user.id), "custom_2":plan.code,
    }
    fields["hash"] = payhere_checkout_hash(settings.PAYHERE_MERCHANT_ID, order_id, plan.amount,
                                             "LKR", settings.PAYHERE_MERCHANT_SECRET)
    logger.info("payhere_order_created order_id=%s user_id=%s plan=%s", order_id, current_user.id, plan.code)
    return PayHereOrderResponse(order_id=order_id, checkout_url=payhere_checkout_url(), fields=fields)

@router.post("/payhere/notify")
async def payhere_notify(request: Request, db: Session = Depends(get_db)):
    require_payhere_configuration()
    form = await request.form()
    values = {key:str(form.get(key, "")) for key in (
        "merchant_id", "order_id", "payment_id", "payhere_amount", "payhere_currency",
        "status_code", "md5sig", "method", "status_message", "custom_1", "custom_2")}
    if values["merchant_id"] != settings.PAYHERE_MERCHANT_ID:
        raise HTTPException(400, "Invalid PayHere notification")
    if not valid_notification_signature(values["md5sig"], merchant_id=values["merchant_id"],
            order_id=values["order_id"], amount=values["payhere_amount"],
            currency=values["payhere_currency"], status_code=values["status_code"]):
        raise HTTPException(400, "Invalid PayHere notification signature")
    payment = db.query(Payment).filter(Payment.order_id == values["order_id"],
                                        Payment.provider == "payhere").with_for_update().first()
    if not payment:
        raise HTTPException(404, "Payment order not found")
    if ((values["custom_1"] and values["custom_1"] != str(payment.user_id)) or
            (values["custom_2"] and values["custom_2"] != payment.plan_code)):
        raise HTTPException(400, "PayHere order metadata mismatch")
    try:
        notified_amount = Decimal(values["payhere_amount"]).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise HTTPException(400, "Invalid PayHere amount") from exc
    if notified_amount != Decimal(payment.amount).quantize(Decimal("0.01")) or values["payhere_currency"] != payment.currency:
        raise HTTPException(400, "PayHere amount or currency mismatch")
    duplicate_id = db.query(Payment).filter(Payment.provider_payment_id == values["payment_id"],
                                            Payment.id != payment.id).first()
    if values["payment_id"] and duplicate_id:
        raise HTTPException(409, "PayHere payment ID is already associated with another order")
    status_map = {"2":"success", "0":"pending", "-1":"cancelled", "-2":"failed", "-3":"chargeback"}
    if values["status_code"] not in status_map:
        raise HTTPException(400, "Unknown PayHere status")
    if payment.status == "success" and values["status_code"] == "2":
        return {"status":"already_processed"}
    payment.status = status_map[values["status_code"]]
    payment.provider_payment_id = values["payment_id"] or payment.provider_payment_id
    payment.payment_method = values["method"][:50] or None
    payment.status_message = values["status_message"][:255] or None
    if values["status_code"] == "2":
        now = utcnow(); plan = payhere_plans()[payment.plan_code]
        active = current_subscription(db, payment.user_id)
        access_start = max(as_utc(active.current_period_end), now) if active else now
        payment.paid_at = payment.paid_at or now
        if payment.subscription is None:
            db.add(Subscription(user_id=payment.user_id, plan_code=payment.plan_code, status="active",
                current_period_start=access_start, current_period_end=access_start + timedelta(days=plan.duration_days),
                source_payment_id=payment.id, cancel_at_period_end=False))
    elif values["status_code"] == "-3" and payment.subscription is not None:
        payment.subscription.status = "chargeback"
        payment.subscription.current_period_end = min(
            as_utc(payment.subscription.current_period_end), utcnow()
        )
    db.commit()
    logger.info("payhere_notification order_id=%s status=%s", payment.order_id, payment.status)
    return {"status":payment.status}


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
            mode="subscription",
            customer_email=current_user.email,
            client_reference_id=order_id,
            metadata={"order_id": order_id, "user_id": str(current_user.id), "plan_code": plan.code},
            subscription_data={"metadata":{"order_id":order_id, "user_id":str(current_user.id), "plan_code":plan.code}},
            line_items=[{"price": price_id_for(plan.code), "quantity": 1}],
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
    return CheckoutResponse(order_id=order_id, provider="stripe", checkout_url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    validate_webhook_configuration()
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook") from exc

    event_id = event["id"]
    if db.query(StripeEvent).filter_by(event_id=event_id).first():
        return {"status": "already_processed"}
    event_type = event["type"]
    obj = event["data"]["object"]
    result = "ignored"
    if event_type == "checkout.session.completed":
        order_id = obj.get("client_reference_id") or obj.get("metadata", {}).get("order_id")
        payment = db.query(Payment).filter_by(order_id=order_id, provider="stripe").with_for_update().first()
        if not payment: raise HTTPException(404, "Payment order not found")
        payment.provider_payment_id = obj.get("id"); payment.status = "pending"
        payment.status_message = "Awaiting verified subscription webhook"; result = "pending"
    elif event_type.startswith("customer.subscription."):
        metadata = obj.get("metadata", {}); user_id = metadata.get("user_id")
        if not user_id:
            payment = db.query(Payment).filter(Payment.order_id == metadata.get("order_id")).first()
            user_id = payment.user_id if payment else None
        if user_id:
            subscription = db.query(Subscription).filter_by(stripe_subscription_id=obj["id"]).first() or Subscription(user_id=int(user_id))
            subscription.plan_code = metadata.get("plan_code", getattr(subscription, "plan_code", None)) or "monthly"
            subscription.status = obj.get("status", "incomplete")
            subscription.stripe_customer_id = obj.get("customer"); subscription.stripe_subscription_id = obj["id"]
            subscription.cancel_at_period_end = bool(obj.get("cancel_at_period_end"))
            start = obj.get("current_period_start")
            end = obj.get("current_period_end")
            if start: subscription.current_period_start = datetime.fromtimestamp(start, timezone.utc)
            if end: subscription.current_period_end = datetime.fromtimestamp(end, timezone.utc)
            db.add(subscription); result = "subscription_updated"
    elif event_type in {"invoice.paid", "invoice.payment_failed"}:
        subscription = db.query(Subscription).filter_by(stripe_subscription_id=obj.get("subscription")).first()
        if subscription:
            subscription.status = "active" if event_type == "invoice.paid" else "past_due"
            result = "invoice_updated"
    db.add(StripeEvent(event_id=event_id, event_type=event_type))
    db.commit()
    return {"status": result}

@router.post("/portal")
def billing_portal(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    validate_checkout_configuration(); configure_stripe()
    subscription = current_subscription(db, current_user.id)
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(404, "No managed subscription found")
    session = stripe.billing_portal.Session.create(customer=subscription.stripe_customer_id,
        return_url=settings.STRIPE_PORTAL_RETURN_URL or f"{settings.FRONTEND_URL.rstrip('/')}/payments")
    return {"url": session.url}


@router.get("/subscription/me", response_model=MyPaymentsOut)
@router.get("/me", response_model=MyPaymentsOut, include_in_schema=False)
def my_payments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    subscription = current_subscription(db, current_user.id)
    payments = db.query(Payment).filter(Payment.user_id == current_user.id).order_by(Payment.created_at.desc()).limit(20).all()
    return MyPaymentsOut(plan_code=subscription.plan_code if subscription else "free", is_premium=subscription is not None,
        subscription=SubscriptionOut.model_validate(subscription) if subscription else None,
        payments=[PaymentOut.model_validate(item) for item in payments])


@router.get("/status/{order_id}", response_model=PaymentStatusOut)
def payment_status(order_id: str, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enforce(request, "payment_status", 60, 60, current_user.id)
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
