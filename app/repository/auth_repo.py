from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.models import User


class AuthRepository:

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            return None

    @staticmethod
    async def create_user(db: AsyncSession, user: User):
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except Exception:
            await db.rollback()
            raise