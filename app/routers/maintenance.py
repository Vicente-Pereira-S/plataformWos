from fastapi import APIRouter, Request, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone, time
import os
import random
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



# Poblar grupo

# Token secreto fijo para protección del endpoint
SECRET_TOKEN = "p0bL4r_GruP0S_2025"

def generate_random_slot():
    start_hour = random.randint(0, 22)
    start_minute = random.choice([0, 30])
    end_hour = start_hour
    end_minute = 30 if start_minute == 0 else 0
    end_hour += 1 if start_minute == 30 else 0
    return time(start_hour, start_minute), time(end_hour, end_minute)

@router.post("/dev/populate-group")
def populate_group_endpoint(
    group_code: str = Query(...),
    num_users: int = Query(60),
    secret_token: str = Query(...),
    db: Session = Depends(get_db)
):
    if secret_token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado")

    group = db.query(models.Group).filter_by(group_code=group_code).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")

    alliances = group.alliances
    days = group.days

    for day in days:
        for i in range(num_users):
            nickname = f"Jugador{i+1}"
            ingame_id = f"{random.randint(10000000, 99999999)}"
            speedups = random.randint(5, 40)
            alliance = random.choice(alliances)

            submission = models.UserSubmission(
                group_day_id=day.id,
                alliance_id=alliance.id,
                nickname=nickname,
                ingame_id=ingame_id,
                speedups=speedups
            )
            db.add(submission)
            db.flush()

            num_slots = random.choice([1, 2])
            for _ in range(num_slots):
                start, end = generate_random_slot()
                slot = models.AvailabilitySlot(
                    submission_id=submission.id,
                    start_time=start,
                    end_time=end
                )
                db.add(slot)

    db.commit()
    return {"message": f"✅ Grupo '{group_code}' poblado con éxito con {num_users} usuarios por día."}