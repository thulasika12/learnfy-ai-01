from datetime import datetime, timezone
from decimal import Decimal
import hashlib

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.database import Base, get_db
from app.config.settings import settings
import app.models  # noqa: F401
from app.models.payment import Payment, Subscription
from app.models.user import User, UserRole
from app.routes import payments
from app.services.payhere_service import checkout_hash, notification_signature
from app.services.rate_limit import _events
from app.utils.dependencies import get_current_user, require_admin

def configure(monkeypatch):
    values = {"PAYHERE_ENABLED":True, "PAYHERE_SANDBOX":True, "PAYMENT_PROVIDER":"payhere",
              "PAYHERE_MERCHANT_ID":"1234567", "PAYHERE_MERCHANT_SECRET":"test-secret-not-real",
              "PAYHERE_CURRENCY":"LKR", "PAYHERE_30_DAY_AMOUNT":"500.00",
              "PAYHERE_365_DAY_AMOUNT":"5000.00", "BACKEND_PUBLIC_URL":"https://tunnel.invalid",
              "FRONTEND_URL":"http://localhost:5173"}
    for key, value in values.items(): monkeypatch.setattr(settings, key, value)

def fixture(monkeypatch, authenticated=True, admin=False):
    _events.clear()
    configure(monkeypatch)
    engine = create_engine("sqlite://", connect_args={"check_same_thread":False}, poolclass=StaticPool)
    Base.metadata.create_all(engine); db = sessionmaker(bind=engine, autoflush=False)()
    user = User(name="Test Student", email="student@example.com", password="x", role=UserRole.student)
    other = User(name="Other User", email="other@example.com", password="x", role=UserRole.student)
    administrator = User(name="Admin", email="admin@example.com", password="x", role=UserRole.admin)
    db.add_all([user, other, administrator]); db.commit()
    app = FastAPI(); app.include_router(payments.router)
    app.dependency_overrides[get_db] = lambda: db
    if authenticated: app.dependency_overrides[get_current_user] = lambda: user
    if admin: app.dependency_overrides[require_admin] = lambda: administrator
    return TestClient(app), db, user, other

def order_payload(plan="premium_30_days", **extra):
    return {"plan_code":plan, "phone":"0771234567", "address":"1 Test Road", "city":"Colombo", **extra}

def signature(order_id, amount="500.00", currency="LKR", status="2"):
    return notification_signature(settings.PAYHERE_MERCHANT_ID, order_id, amount, currency,
                                  status, settings.PAYHERE_MERCHANT_SECRET)

def notification(order_id, amount="500.00", currency="LKR", status="2", payment_id="PH-1", md5sig=None):
    return {"merchant_id":settings.PAYHERE_MERCHANT_ID, "order_id":order_id, "payment_id":payment_id,
            "payhere_amount":amount, "payhere_currency":currency, "status_code":status,
            "md5sig":md5sig or signature(order_id, amount, currency, status), "method":"VISA",
            "status_message":"Test notification"}

def create_order(client, plan="premium_30_days", **extra):
    response = client.post("/payments/payhere/create-order", json=order_payload(plan, **extra))
    assert response.status_code == 201, response.text
    return response.json()

def test_sandbox_localhost_configuration_and_shared_checkout(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setattr(settings, "BACKEND_PUBLIC_URL", "http://localhost:8000")
    client, db, *_ = fixture(monkeypatch)
    monkeypatch.setattr(settings, "BACKEND_PUBLIC_URL", "http://localhost:8000")
    try:
        config = client.get("/payments/config")
        assert config.status_code == 200
        assert config.json()["configured"] is True
        assert config.json()["gatewayReady"] is True
        assert config.json()["publicCallbackReady"] is False
        response = client.post("/payments/checkout", json=order_payload())
        assert response.status_code == 201, response.text
        assert response.json()["checkout_url"] == "https://sandbox.payhere.lk/pay/checkout"
        assert response.json()["fields"]["notify_url"] == "http://localhost:8000/payments/payhere/notify"
    finally:
        db.close()

def test_order_requires_login(monkeypatch):
    client, db, *_ = fixture(monkeypatch, authenticated=False)
    try: assert client.post("/payments/payhere/create-order", json=order_payload()).status_code == 401
    finally: db.close()

def test_invalid_plan_rejected_and_amount_not_trusted(monkeypatch):
    client, db, *_ = fixture(monkeypatch)
    try:
        assert client.post("/payments/payhere/create-order", json=order_payload("monthly")).status_code == 422
        created = create_order(client, amount="0.01")
        payment = db.query(Payment).filter_by(order_id=created["order_id"]).one()
        assert payment.amount == Decimal("500.00")
        assert created["fields"]["amount"] == "500.00"
    finally: db.close()

def test_checkout_hash_matches_official_formula(monkeypatch):
    configure(monkeypatch)
    inner = hashlib.md5(b"test-secret-not-real").hexdigest().upper()
    expected = hashlib.md5(f"1234567ORDER1500.00LKR{inner}".encode()).hexdigest().upper()
    assert checkout_hash("1234567", "ORDER1", Decimal("500"), "LKR", "test-secret-not-real") == expected

def test_valid_success_activates_and_duplicate_is_idempotent(monkeypatch):
    client, db, user, _ = fixture(monkeypatch)
    try:
        created = create_order(client); data = notification(created["order_id"])
        first = client.post("/payments/payhere/notify", data=data)
        expiry = db.query(Subscription).filter_by(user_id=user.id).one().current_period_end
        second = client.post("/payments/payhere/notify", data=data)
        assert first.json()["status"] == "success"
        assert second.json()["status"] == "already_processed"
        assert db.query(Subscription).filter_by(user_id=user.id).count() == 1
        assert db.query(Subscription).filter_by(user_id=user.id).one().current_period_end == expiry
    finally: db.close()

def test_invalid_signature_amount_and_currency_are_rejected(monkeypatch):
    client, db, *_ = fixture(monkeypatch)
    try:
        one = create_order(client)
        assert client.post("/payments/payhere/notify", data=notification(one["order_id"], md5sig="BAD")).status_code == 400
        assert client.post("/payments/payhere/notify", data=notification(one["order_id"], amount="1.00")).status_code == 400
        assert client.post("/payments/payhere/notify", data=notification(one["order_id"], currency="USD")).status_code == 400
        mismatched = notification(one["order_id"]); mismatched["custom_1"] = "999"
        assert client.post("/payments/payhere/notify", data=mismatched).status_code == 400
    finally: db.close()

def test_failed_and_cancelled_do_not_activate(monkeypatch):
    client, db, user, _ = fixture(monkeypatch)
    try:
        for index, code in enumerate(("-1", "-2"), 1):
            created = create_order(client)
            response = client.post("/payments/payhere/notify", data=notification(
                created["order_id"], status=code, payment_id=f"PH-{index}"))
            assert response.json()["status"] in {"cancelled", "failed"}
        assert db.query(Subscription).filter_by(user_id=user.id).count() == 0
    finally: db.close()

def test_chargeback_revokes_access_after_success(monkeypatch):
    client, db, user, _ = fixture(monkeypatch)
    try:
        created = create_order(client)
        client.post("/payments/payhere/notify", data=notification(created["order_id"], payment_id="PH-C"))
        response = client.post("/payments/payhere/notify", data=notification(
            created["order_id"], status="-3", payment_id="PH-C"))
        subscription = db.query(Subscription).filter_by(user_id=user.id).one()
        assert response.json()["status"] == "chargeback"
        assert subscription.status == "chargeback"
        assert db.query(Payment).filter_by(order_id=created["order_id"]).one().status == "chargeback"
    finally: db.close()

def test_existing_premium_is_extended(monkeypatch):
    client, db, user, _ = fixture(monkeypatch)
    try:
        first = create_order(client); client.post("/payments/payhere/notify", data=notification(first["order_id"], payment_id="PH-A"))
        first_end = db.query(Subscription).filter_by(user_id=user.id).one().current_period_end
        second = create_order(client); client.post("/payments/payhere/notify", data=notification(second["order_id"], payment_id="PH-B"))
        latest = db.query(Subscription).filter_by(user_id=user.id).order_by(Subscription.current_period_end.desc()).first()
        start = latest.current_period_start
        assert (start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start) == (first_end.replace(tzinfo=timezone.utc) if first_end.tzinfo is None else first_end)
    finally: db.close()

def test_status_prevents_idor_and_admin_lists_payhere(monkeypatch):
    client, db, user, other = fixture(monkeypatch, admin=True)
    try:
        created = create_order(client)
        client.app.dependency_overrides[get_current_user] = lambda: other
        assert client.get(f"/payments/status/{created['order_id']}").status_code == 404
        response = client.get("/payments/admin/transactions")
        assert response.status_code == 200
        assert response.json()[0]["provider"] == "payhere"
    finally: db.close()
