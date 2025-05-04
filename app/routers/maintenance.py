from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import os

from app import models
from app.database import get_db

router = APIRouter()

# Token secreto que debe venir en el header de la petición
SECRET_MAINTENANCE_TOKEN = os.getenv("MAINTENANCE_SECRET_TOKEN")

@router.post("/maintenance/purge-inactive-users")
def purge_inactive_users(request: Request, db: Session = Depends(get_db)):
    # Verificamos el token en los headers
    token = request.headers.get("X-Maintenance-Token")
    if token != SECRET_MAINTENANCE_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Calculamos el umbral de inactividad (90 días sin iniciar sesión)
    threshold = datetime.now(timezone.utc) - timedelta(days=90)

    # Buscamos usuarios inactivos
    inactive_users = db.query(models.User).filter(models.User.last_login < threshold).all()
    deleted_count = 0

    for user in inactive_users:
        db.delete(user)
        deleted_count += 1

    db.commit()
    return {"message": f"Usuarios eliminados: {deleted_count}"}
