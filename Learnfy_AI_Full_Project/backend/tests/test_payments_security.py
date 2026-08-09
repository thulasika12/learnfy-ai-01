from types import SimpleNamespace
from unittest.mock import patch

import stripe
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.database import Base, get_db
from app.config.settings import settings
import app.models  # noqa: F401
from app.models.payment import Payment
from app.models.user import User, UserRole
from app.routes import payments
from app.utils.dependencies import get_current_user

def make_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    user = User(name="Payment Test", email="payment@example.com", password="x", role=UserRole.student)
    session.add(user); session.commit(); session.refresh(user)
    app = FastAPI(); app.include_router(payments.router)
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app), session, user

def configure_test_stripe(monkeypatch):
    monkeypatch.setattr(settings, "PAYMENTS_ENABLED", True)
    monkeypatch.setattr(settings, "PAYMENT_PROVIDER", "stripe")
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_not_real")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_not_real")
    monkeypatch.setattr(settings, "STRIPE_MONTHLY_PRICE_ID", "price_test_monthly")
    monkeypatch.setattr(settings, "STRIPE_YEARLY_PRICE_ID", "price_test_yearly")

def test_checkout_disabled_by_default():
    client, session, _ = make_client()
    try:
        with patch.object(settings, "PAYMENTS_ENABLED", False):
            response = client.post("/payments/checkout", json={"plan_code":"monthly"})
        assert response.status_code == 503
        assert response.json()["detail"] == "Payments are currently unavailable"
    finally:
        session.close()

def test_checkout_uses_subscription_and_server_price(monkeypatch):
    configure_test_stripe(monkeypatch)
    client, session, _ = make_client()
    try:
        with patch("app.routes.payments.stripe.checkout.Session.create", return_value=SimpleNamespace(id="cs_test", url="https://stripe.invalid/test")) as create:
            response = client.post("/payments/checkout", json={"plan_code":"monthly"})
        assert response.status_code == 201, response.text
        assert response.json()["provider"] == "stripe"
        kwargs = create.call_args.kwargs
        assert kwargs["mode"] == "subscription"
        assert kwargs["line_items"] == [{"price":"price_test_monthly", "quantity":1}]
        assert "price_data" not in kwargs["line_items"][0]
    finally:
        session.close()

def test_webhook_rejects_invalid_signature(monkeypatch):
    configure_test_stripe(monkeypatch)
    client, session, _ = make_client()
    try:
        error = stripe.SignatureVerificationError("bad signature", "bad")
        with patch("app.routes.payments.stripe.Webhook.construct_event", side_effect=error):
            response = client.post("/payments/webhook", content=b"{}", headers={"stripe-signature":"bad"})
        assert response.status_code == 400
    finally:
        session.close()

def test_webhook_event_is_idempotent(monkeypatch):
    configure_test_stripe(monkeypatch)
    client, session, user = make_client()
    payment = Payment(user_id=user.id, order_id="LFY-TEST", provider="stripe", plan_code="monthly",
                      amount=500, currency="LKR", status="initiated")
    session.add(payment); session.commit()
    event = {"id":"evt_test_once", "type":"checkout.session.completed", "data":{"object":{
        "id":"cs_test", "client_reference_id":"LFY-TEST", "metadata":{}}}}
    try:
        with patch("app.routes.payments.stripe.Webhook.construct_event", return_value=event):
            first = client.post("/payments/webhook", content=b"{}", headers={"stripe-signature":"test"})
            second = client.post("/payments/webhook", content=b"{}", headers={"stripe-signature":"test"})
        assert first.json()["status"] == "pending"
        assert second.json()["status"] == "already_processed"
    finally:
        session.close()
