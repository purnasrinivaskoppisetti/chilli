from fastapi import HTTPException
from app.models.models import User
from app.repository.auth_repo import AuthRepository
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:

    @staticmethod
    async def register(payload, db):

        existing_user = await AuthRepository.get_user_by_email(db, payload.email)

        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            password_hash=hash_password(payload.password)
        )

        await AuthRepository.create_user(db, user)

        return {
            "success": True,
            "message": "User registered successfully"
        }

    @staticmethod
    async def login(payload, db):

        user = await AuthRepository.get_user_by_email(db, payload.email)

        if not user:
            raise HTTPException(status_code=400, detail="Invalid email or password")

        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid email or password")

        token = create_access_token({
            "user_id": user.id,
            "email": user.email
        })

        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": token,
                "token_type": "bearer"
            }
        }