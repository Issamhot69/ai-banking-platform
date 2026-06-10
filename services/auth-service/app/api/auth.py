from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    generate_totp_secret, get_totp_uri, verify_totp,
)
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, UserResponse, Enable2FAResponse,
    Verify2FARequest, KYCUpdateRequest,
)
from app.utils.dependencies import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    user = User(
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    if user.is_2fa_enabled:
        if not payload.totp_code:
            raise HTTPException(status_code=400, detail="Code 2FA requis")
        if not verify_totp(user.totp_secret, payload.totp_code):
            raise HTTPException(status_code=401, detail="Code 2FA invalide")

    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    await redis.setex(
        f"refresh:{user.id}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        refresh_token,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    token_data = decode_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token invalide")

    user_id = token_data.get("sub")
    stored = await redis.get(f"refresh:{user_id}")
    if stored != payload.refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token expiré ou révoqué")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    new_data = {"sub": str(user.id), "email": user.email}
    new_access = create_access_token(new_data)
    new_refresh = create_refresh_token(new_data)

    await redis.setex(
        f"refresh:{user.id}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        new_refresh,
    )

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    await redis.delete(f"refresh:{current_user.id}")
    return {"message": "Déconnexion réussie"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/2fa/enable", response_model=Enable2FAResponse)
async def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=400, detail="2FA déjà activé")

    secret = generate_totp_secret()
    qr_uri = get_totp_uri(secret, current_user.email)
    current_user.totp_secret = secret
    await db.commit()

    return Enable2FAResponse(
        secret=secret,
        qr_uri=qr_uri,
        message="Scannez le QR code avec Google Authenticator puis confirmez avec /2fa/verify",
    )


@router.post("/2fa/verify")
async def verify_2fa(
    payload: Verify2FARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA non initialisé")
    if not verify_totp(current_user.totp_secret, payload.code):
        raise HTTPException(status_code=401, detail="Code invalide")

    current_user.is_2fa_enabled = True
    await db.commit()
    return {"message": "2FA activé avec succès"}


@router.put("/kyc")
async def update_kyc(
    payload: KYCUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.national_id = payload.national_id
    current_user.kyc_status = "pending"
    await db.commit()
    return {"message": "KYC soumis, en cours de vérification", "status": "pending"}
