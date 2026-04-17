from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import RegisterSchema, LoginSchema
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register")
async def register(payload: RegisterSchema, db: AsyncSession = Depends(get_db)):
    return await AuthService.register(payload, db)


@router.post("/login")
async def login(payload: LoginSchema, db: AsyncSession = Depends(get_db)):
    return await AuthService.login(payload, db)