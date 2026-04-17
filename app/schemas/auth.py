from pydantic import BaseModel, EmailStr

class RegisterSchema(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None