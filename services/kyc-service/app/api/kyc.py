from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import uuid
import os
import base64
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.kyc import KYCApplication
from app.schemas.kyc import KYCResponse, KYCReviewRequest, KYCStatsResponse
from app.utils.dependencies import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/kyc", tags=["KYC"])

UPLOAD_DIR = "/tmp/kyc_documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_file(file: UploadFile, user_id: str, doc_type: str) -> str:
    ext = file.filename.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Format non supporté: {ext}")
    filename = f"{user_id}_{doc_type}_{uuid.uuid4().hex[:8]}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 10MB)")
    with open(path, "wb") as f:
        f.write(content)
    return f"/kyc/documents/{filename}"


async def verify_with_ai(application: KYCApplication) -> dict:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Analyse cette demande KYC bancaire et donne un avis de vérification:
                
Nom: {application.first_name} {application.last_name}
Type de document: {application.document_type}
Numéro: {application.document_number}
Date de naissance: {application.date_of_birth}
Nationalité: {application.nationality}
Adresse: {application.address}

Réponds en JSON avec:
- is_valid (bool)
- confidence_score (0-100)
- risk_level (low/medium/high)
- flags (liste de problèmes éventuels)
- recommendation (approve/review/reject)
- notes (string)

Réponds UNIQUEMENT en JSON valide."""
            }]
        )
        import json
        result = json.loads(message.content[0].text)
        return result
    except Exception as e:
        return {
            "is_valid": True,
            "confidence_score": 75,
            "risk_level": "low",
            "flags": [],
            "recommendation": "review",
            "notes": f"Vérification manuelle requise (AI non disponible: {str(e)[:50]})"
        }


@router.post("/submit", response_model=KYCResponse, status_code=201)
async def submit_kyc(
    document_type: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    document_number: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    nationality: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    document_front: UploadFile = File(...),
    document_back: Optional[UploadFile] = File(None),
    selfie: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Vérifier si une demande existe déjà
    existing = await db.execute(
        select(KYCApplication).where(
            KYCApplication.user_id == current_user["id"],
            KYCApplication.status.in_(["pending", "in_review", "verified"])
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Une demande KYC est déjà en cours ou approuvée")

    # Sauvegarder les fichiers
    front_url = await save_file(document_front, current_user["id"], "front")
    back_url = await save_file(document_back, current_user["id"], "back") if document_back else None
    selfie_url = await save_file(selfie, current_user["id"], "selfie") if selfie else None

    application = KYCApplication(
        user_id=current_user["id"],
        document_type=document_type,
        document_number=document_number,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        nationality=nationality,
        address=address,
        document_front_url=front_url,
        document_back_url=back_url,
        selfie_url=selfie_url,
        status="in_review",
    )

    db.add(application)
    await db.flush()

    # Vérification AI
    ai_result = await verify_with_ai(application)
    application.ai_verification_result = ai_result

    # Auto-approve si confiance élevée
    if ai_result.get("confidence_score", 0) >= 90 and ai_result.get("recommendation") == "approve":
        application.status = "verified"
        application.reviewed_at = datetime.now(timezone.utc)
        application.reviewed_by = "AI Auto-Verification"

    await db.commit()
    await db.refresh(application)
    return application


@router.get("/status", response_model=KYCResponse)
async def get_kyc_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KYCApplication)
        .where(KYCApplication.user_id == current_user["id"])
        .order_by(KYCApplication.created_at.desc())
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Aucune demande KYC trouvée")
    return application


@router.get("/admin/applications", response_model=list[KYCResponse])
async def list_all_applications(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(KYCApplication).order_by(KYCApplication.created_at.desc())
    if status:
        query = query.where(KYCApplication.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/admin/applications/{application_id}/review", response_model=KYCResponse)
async def review_application(
    application_id: uuid.UUID,
    payload: KYCReviewRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(KYCApplication).where(KYCApplication.id == application_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Demande introuvable")

    if payload.action == "approve":
        application.status = "verified"
    elif payload.action == "reject":
        application.status = "rejected"
        application.rejection_reason = payload.reason
    else:
        raise HTTPException(status_code=400, detail="Action invalide: approve ou reject")

    application.reviewed_at = datetime.now(timezone.utc)
    application.reviewed_by = current_user["email"]

    await db.commit()
    await db.refresh(application)
    return application


@router.get("/admin/stats", response_model=KYCStatsResponse)
async def get_kyc_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = await db.execute(select(func.count(KYCApplication.id)))
    pending = await db.execute(select(func.count(KYCApplication.id)).where(KYCApplication.status == "pending"))
    in_review = await db.execute(select(func.count(KYCApplication.id)).where(KYCApplication.status == "in_review"))
    verified = await db.execute(select(func.count(KYCApplication.id)).where(KYCApplication.status == "verified"))
    rejected = await db.execute(select(func.count(KYCApplication.id)).where(KYCApplication.status == "rejected"))

    return KYCStatsResponse(
        total=total.scalar() or 0,
        pending=pending.scalar() or 0,
        in_review=in_review.scalar() or 0,
        verified=verified.scalar() or 0,
        rejected=rejected.scalar() or 0,
    )


@router.get("/documents/{filename}")
async def get_document(filename: str, current_user: dict = Depends(get_current_user)):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Document introuvable")
    from fastapi.responses import FileResponse
    return FileResponse(path)
