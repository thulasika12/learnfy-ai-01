"""Atomic, server-side AI quotas derived from verified subscription state."""
from datetime import date, datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.config.settings import settings
from app.models.entitlement import DailyAIUsage
from app.models.payment import Subscription

FEATURES = ("ai_chat", "summary", "quiz", "flashcards", "study_planner")

def is_premium(db: Session, user_id: int) -> bool:
    now = datetime.now(timezone.utc)
    return db.query(Subscription).filter(Subscription.user_id == user_id,
        Subscription.status.in_(("active", "trialing")), Subscription.current_period_end > now).first() is not None

def limit_for(feature: str, premium: bool) -> int:
    names = {"ai_chat":"AI_CHAT", "summary":"SUMMARY", "quiz":"QUIZ",
             "flashcards":"FLASHCARDS", "study_planner":"STUDY_PLANNER"}
    if feature not in names:
        raise ValueError("Unknown AI feature")
    return getattr(settings, f"{'PREMIUM' if premium else 'FREE'}_{names[feature]}_LIMIT")

def consume(db: Session, user_id: int, feature: str) -> dict:
    premium = is_premium(db, user_id)
    limit = limit_for(feature, premium)
    today = date.today()
    usage = db.query(DailyAIUsage).filter_by(user_id=user_id, feature=feature, usage_date=today).with_for_update().first()
    if usage is None:
        usage = DailyAIUsage(user_id=user_id, feature=feature, usage_date=today, usage_count=0)
        db.add(usage); db.flush()
    if usage.usage_count >= limit:
        db.rollback()
        raise HTTPException(429, detail={"code":"daily_ai_limit_reached", "feature":feature,
            "limit":limit, "message":"Daily limit reached. Upgrade your plan or try again tomorrow."})
    usage.usage_count += 1
    db.commit()
    return {"used": usage.usage_count, "limit": limit, "remaining": limit - usage.usage_count}

def snapshot(db: Session, user_id: int) -> dict:
    premium = is_premium(db, user_id); today = date.today()
    rows = {row.feature: row.usage_count for row in db.query(DailyAIUsage).filter_by(user_id=user_id, usage_date=today)}
    return {"plan":"premium" if premium else "free", "date":str(today), "features":{
        feature:{"used":rows.get(feature,0), "limit":limit_for(feature,premium),
                 "remaining":max(0,limit_for(feature,premium)-rows.get(feature,0))} for feature in FEATURES}}
