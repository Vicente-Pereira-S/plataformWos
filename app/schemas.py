from pydantic import BaseModel, EmailStr
from typing import Optional

# ------------------------------
# Esquema base para el modelo de usuario
# ------------------------------
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None


# ------------------------------
# Esquema para la creación de usuarios
# ------------------------------
class UserCreate(UserBase):
    password: str


# ------------------------------
# Esquema para la respuesta del usuario
# ------------------------------
class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool

    model_config = {
        "from_attributes": True  # Equivalente moderno de orm_mode en Pydantic v2
    }
