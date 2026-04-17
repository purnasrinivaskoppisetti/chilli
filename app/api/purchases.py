from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.purchase import PurchaseCreateSchema
from app.services.purchase_service import PurchaseService
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/preview")
async def preview_purchase(
    payload: PurchaseCreateSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    data = await PurchaseService.calculate_preview(payload)

    return {
        "success": True,
        "message": "Preview calculated successfully",
        "data": data
    }


@router.post("/create")
async def create_purchase(
    payload: PurchaseCreateSchema,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    result = await PurchaseService.create_purchase(payload, db, user.id)

    return {
        "success": True,
        "message": "Purchase saved successfully",
        "data": result
    }