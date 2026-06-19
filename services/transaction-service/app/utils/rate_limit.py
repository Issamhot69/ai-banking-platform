from fastapi import HTTPException, Request
import redis.asyncio as aioredis


async def rate_limit(request: Request, redis: aioredis.Redis, max_calls: int = 10, window_seconds: int = 60):
    """Rate limiter par utilisateur basé sur Redis — sliding window.
    Lève HTTPException 429 si la limite est dépassée."""
    user_id = None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        from jose import jwt, JWTError
        import os
        try:
            token = auth.split(" ")[1]
            payload = jwt.decode(token, os.environ.get("SECRET_KEY", ""), algorithms=["HS256"])
            user_id = payload.get("sub")
        except JWTError:
            pass

    if not user_id:
        return  # Pas authentifié — laisse l'auth middleware gérer

    key = f"rate_limit:transfer:{user_id}"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, window_seconds)

    if current > max_calls:
        retry_after = await redis.ttl(key)
        raise HTTPException(
            status_code=429,
            detail=f"Trop de requêtes — limite de {max_calls} appels par {window_seconds}s. Réessayez dans {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )
