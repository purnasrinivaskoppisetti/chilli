from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from app.models.models import User
from app.repository.auth_repo import AuthRepository
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:

    @staticmethod
    async def register(payload, db):
        try:
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

        except HTTPException as e:
            raise e

        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")

        except Exception:
            raise HTTPException(status_code=500, detail="Registration failed")

    @staticmethod
    async def login(payload, db):
        try:
            user = await AuthRepository.get_user_by_email(db, payload.email)

            if not user:
                raise HTTPException(status_code=400, detail="Invalid email or password")

            # 🔴 IMPORTANT FIX (argon2 issue safe)
            try:
                password_valid = verify_password(payload.password, user.password_hash)
            except Exception:
                raise HTTPException(status_code=500, detail="Password verification failed")

            if not password_valid:
                raise HTTPException(status_code=400, detail="Invalid email or password")

            try:
                token = create_access_token({
                    "user_id": user.id,
                    "email": user.email
                })
            except Exception:
                raise HTTPException(status_code=500, detail="Token generation failed")

            return {
                "success": True,
                "message": "Login successful",
                "data": {
                    "access_token": token,
                    "token_type": "bearer"
                }
            }

        except HTTPException as e:
            raise e

        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")

        except Exception:
            raise HTTPException(status_code=500, detail="Login failed")