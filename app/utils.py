from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app import models
import os
from scipy.optimize import linear_sum_assignment
import numpy as np


def delete_inactive_users(db: Session):
    """
    Elimina usuarios que no han iniciado sesión en más de 90 días
    y que no son creadores de ningún grupo.
    """
    INACTIVE_DAYS_THRESHOLD = int(os.getenv("INACTIVE_DAYS_THRESHOLD", 90))
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=INACTIVE_DAYS_THRESHOLD)


    # Buscar usuarios inactivos y que NO sean creadores de grupo
    users_to_delete = db.query(models.User).filter(
        models.User.last_login < cutoff_date,
        ~models.User.groups.any(models.GroupMember.role == "creator")  # Asegura que no son creadores
    ).all()

    deleted_ids = [user.id for user in users_to_delete]

    for user in users_to_delete:
        db.delete(user)

    db.commit()
    return deleted_ids




def assign_slots_with_hungarian(submissions):
    """
    Asigna 48 bloques de 30 minutos a usuarios usando el algoritmo húngaro.
    
    Parámetros:
        submissions: lista de dicts con estructura:
            {
                "nickname": str,
                "ingame_id": str | None,
                "speedups": int,
                "alliance": str,
                "availability": [ (start_block:int, end_block:int), ... ]
            }

    Retorna:
        Listado de asignaciones:
        [
            {
                "hour_block": int (0-47),
                "nickname": str,
                "ingame_id": str | None,
                "alliance": str,
                "speedups": int,
                "availability_str": str (ej: "00:00–08:00, 14:00–15:00")
            },
            ...
        ]
    """
    MAX_BLOCKS = 48
    cost_matrix = np.full((len(submissions), MAX_BLOCKS), 9999)

    def block_to_time(b):
        h, m = divmod(b * 30, 60)
        return f"{h:02d}:{m:02d}"

    # Rellenar matriz de costo
    for i, sub in enumerate(submissions):
        for start, end in sub["availability"]:
            for b in range(start, end):  # intervalo abierto: end no incluido
                if b < MAX_BLOCKS:
                    cost_matrix[i, b] = -sub["speedups"]

    # Aplicar algoritmo húngaro
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    results = []
    for u_idx, block in zip(row_ind, col_ind):
        if cost_matrix[u_idx, block] == 9999:
            continue  # No se pudo asignar

        user = submissions[u_idx]
        availability_str = ", ".join([
            f"{block_to_time(start)}–{block_to_time(end)}"
            for (start, end) in user["availability"]
        ])

        results.append({
            "hour_block": block,
            "nickname": user["nickname"],
            "ingame_id": user.get("ingame_id"),
            "alliance": user["alliance"],
            "speedups": user["speedups"],
            "availability_str": availability_str,
        })

    return sorted(results, key=lambda x: x["hour_block"])


def run_assignment_for_group_day(db: Session, group_day_id: int):
    """
    Ejecuta la asignación de citas para un día específico del grupo usando el algoritmo húngaro.

    Retorna: lista de 48 asignaciones (o menos si no hay suficientes postulantes).
    """
    from app.models import UserSubmission, AvailabilitySlot

    submissions = db.query(UserSubmission).filter(UserSubmission.group_day_id == group_day_id).all()
    if not submissions:
        return []

    formatted = []
    for sub in submissions:
        blocks = []
        for slot in sub.availability:
            start_block = slot.start_time.hour * 2 + (1 if slot.start_time.minute >= 30 else 0)
            end_block = slot.end_time.hour * 2 + (1 if slot.end_time.minute >= 30 else 0)
            blocks.append((start_block, end_block))

        formatted.append({
            "nickname": sub.nickname,
            "ingame_id": sub.ingame_id,
            "speedups": sub.speedups,
            "alliance": sub.alliance.name,
            "availability": blocks
        })

    return assign_slots_with_hungarian(formatted)
