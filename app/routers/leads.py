from fastapi import APIRouter

from app.schemas import LeadCreateRequest, LeadCreateResponse


router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("", response_model=LeadCreateResponse)
def create_lead(payload: LeadCreateRequest):
    # Production version:
    # 1. Save this lead to PostgreSQL/CRM.
    # 2. Send notification email.
    # 3. Add anti-spam protection.
    # 4. Track marketing attribution.
    return {
        "status": "success",
        "message": f"Thanks {payload.name}, we received your request.",
    }
