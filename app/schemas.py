from pydantic import BaseModel, EmailStr
from typing import Optional


# Para crear un nuevo usuario
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None


# Para login
class UserLogin(BaseModel):
    username: str
    password: str


# Para mostrar info del usuario (sin contraseña)
class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True
