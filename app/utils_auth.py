import bcrypt
from jose import JWTError, jwt
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from app import models
from app.database import get_db

load_dotenv()

# Clave secreta para JWT (asegúrate de tenerla en tu .env)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "changeme")
ALGORITHM = "HS256"

# ---------------------------
# FUNCIONES DE AUTENTICACIÓN
# ---------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token.replace("Bearer ", ""), SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except JWTError:
        return None


def get_current_user_optional(request: Request):
    return decode_token_from_cookie(request)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    user_id = decode_token_from_cookie(request)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user

def mask_email(email: str) -> str:
    usuario, dominio = email.split("@")
    oculto_usuario = usuario[:5] + "*" * (len(usuario) - 5)
    oculto_dominio = dominio[:2] + "*" * (len(dominio) - 2)
    return f"{oculto_usuario}@{oculto_dominio}"