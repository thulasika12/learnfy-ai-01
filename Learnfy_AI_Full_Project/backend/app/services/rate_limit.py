"""Reusable fixed-window limiter: Redis in production, memory only outside production."""
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock
from fastapi import HTTPException, Request
from app.config.settings import settings

_events = defaultdict(deque)
_lock = Lock()
_redis = None

def client_ip(request: Request) -> str:
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if forwarded: return forwarded
    return request.client.host if request.client else "unknown"

def enforce(request: Request, scope: str, limit: int, window_seconds: int, user_id: int | None = None):
    key = f"learnfy:rate:{scope}:{user_id or client_ip(request)}"
    now = int(datetime.now(timezone.utc).timestamp())
    if settings.REDIS_URL:
        global _redis
        if _redis is None:
            from redis import Redis
            _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        count = _redis.incr(key)
        if count == 1: _redis.expire(key, window_seconds)
        retry = max(1, _redis.ttl(key))
    else:
        if settings.ENVIRONMENT.lower() == "production":
            raise RuntimeError("Redis rate limiting is required in production")
        with _lock:
            bucket = _events[key]
            while bucket and bucket[0] <= now - window_seconds: bucket.popleft()
            count = len(bucket) + 1
            retry = max(1, window_seconds - (now - bucket[0])) if bucket else window_seconds
            if count <= limit: bucket.append(now)
    if count > limit:
        raise HTTPException(429, "Too many requests. Please try again later.", headers={"Retry-After":str(retry)})
