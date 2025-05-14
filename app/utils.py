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



# ------------------------------
# Asignación con algoritmo húngaro
# ------------------------------


def assign_slots_with_hungarian(submissions):
    """
    Asigna 48 bloques de 30 minutos a los 48 usuarios con más speedups.

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
        - Lista de asignaciones ordenadas por hora.
        - Lista de usuarios no asignados (de los 48 seleccionados).
    """
    import numpy as np
    from scipy.optimize import linear_sum_assignment

    MAX_BLOCKS = 48

    # Tomar solo los 48 con más speedups
    top_48 = sorted(submissions, key=lambda x: x["speedups"], reverse=True)[:MAX_BLOCKS]

    cost_matrix = np.full((len(top_48), MAX_BLOCKS), 9999)

    def block_to_time(b):
        h, m = divmod(b * 30, 60)
        return f"{h:02d}:{m:02d}"

    for i, sub in enumerate(top_48):
        for start, end in sub["availability"]:
            # Caso especial: si start == end → solo ese bloque
            if start == end:
                if 0 <= start < MAX_BLOCKS:
                    cost_matrix[i, start] = -sub["speedups"]
            else:
                # Caso normal: incluir también el bloque que inicia en "end"
                for b in range(start, end + 1):
                    if 0 <= b < MAX_BLOCKS:
                        cost_matrix[i, b] = -sub["speedups"]

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    results = []
    asignados_idx = set()

    for u_idx, block in zip(row_ind, col_ind):
        if cost_matrix[u_idx, block] == 9999:
            continue

        user = top_48[u_idx]
        asignados_idx.add(u_idx)

        availability_str = ", ".join([
            f"{block_to_time(start)}–{block_to_time(end)}"
            for (start, end) in user["availability"]
        ])

        results.append({
            "hour_block": int(block),
            "nickname": user["nickname"],
            "ingame_id": user.get("ingame_id"),
            "alliance": user["alliance"],
            "speedups": int(user["speedups"]),
            "availability_str": availability_str,
        })

    # Solo mostrar como no asignados a los que estaban en el top 48 y no recibieron bloque
    no_asignados = []
    for i, sub in enumerate(top_48):
        if i not in asignados_idx:
            no_asignados.append({
                "nickname": sub["nickname"],
                "ingame_id": sub.get("ingame_id"),
                "alliance": sub["alliance"],
                "speedups": int(sub["speedups"])
            })

    return sorted(results, key=lambda x: x["hour_block"]), no_asignados


def run_assignment_for_group_day(db: Session, group_day_id: int):
    """
    Ejecuta la asignación de citas para un día específico del grupo usando el algoritmo húngaro.

    Retorna:
        - Lista de asignaciones exitosas (dicts)
        - Lista de usuarios no asignados (dicts)
    """
    from app.models import UserSubmission

    submissions = db.query(UserSubmission).filter(UserSubmission.group_day_id == group_day_id).all()
    if not submissions:
        return [], []

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
