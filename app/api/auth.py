from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth import RegisterSchema, LoginSchema
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register")
async def register(payload: RegisterSchema, db: AsyncSession = Depends(get_db)):
    try:
        return await AuthService.register(payload, db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.post("/login")
async def login(payload: LoginSchema, db: AsyncSession = Depends(get_db)):
    try:
        return await AuthService.login(payload, db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong")