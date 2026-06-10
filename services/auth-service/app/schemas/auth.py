from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import uuid
import re


class RegisterRequest(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    password: str
    first_name: str
    last_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Minimum 8 caractères")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Au moins une majuscule")
        if not re.search(r"[0-9]", v):
            raise ValueError("Au moins un chiffre")
        return v

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v):
        if v and not re.match(r"^\+?[1-9]\d{7,14}$", v):
            raise ValueError("Format téléphone invalide")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    phone: Optional[str]
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    kyc_status: str
    is_2fa_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Enable2FAResponse(BaseModel):
    secret: str
    qr_uri: str
    message: str


class Verify2FARequest(BaseModel):
    code: str


class KYCUpdateRequest(BaseModel):
    national_id: str
    date_of_birth: str
    status: str = "pending"
