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


def seleccionar_top_48(submissions, cupos=None):
    """
    Selecciona las 48 submissions que serán usadas por el algoritmo húngaro,
    en función de los cupos por alianza (si se definen).

    Retorna:
        - Lista de submissions seleccionadas (máximo 48)
        - Diccionario de cupos restantes (incluye B)
    """
    MAX_BLOCKS = 48
    submissions_sorted = sorted(submissions, key=lambda x: x["speedups"], reverse=True)

    # Si no hay cupos definidos, usar el comportamiento actual
    if cupos is None:
        return submissions_sorted[:MAX_BLOCKS], {}

    # Inicializar variables de trabajo
    cupos_restantes = dict(cupos)  # copia segura
    total_cupos_fijos = sum(v for v in cupos_restantes.values())
    B = MAX_BLOCKS - total_cupos_fijos
    top_48 = []

    for sub in submissions_sorted:
        alliance = sub["alliance"]

        if alliance in cupos_restantes:
            if cupos_restantes[alliance] > 0:
                cupos_restantes[alliance] -= 1
                top_48.append(sub)
        else:
            if B > 0:
                B -= 1
                top_48.append(sub)

        # Salida anticipada si ya tenemos 48 asignaciones
        if len(top_48) >= MAX_BLOCKS:
            break

    # Agregar B al resultado
    cupos_restantes["B"] = B

    return top_48, cupos_restantes


def assign_slots_with_hungarian(submissions):
    """
    Asigna 48 bloques de 30 minutos a los 48 usuarios con más speedups.
    (la lógica del Hungarian permanece intacta)
    """
    import numpy as np
    from scipy.optimize import linear_sum_assignment

    MAX_BLOCKS = 48
    top_48 = sorted(submissions, key=lambda x: x["speedups"], reverse=True)[:MAX_BLOCKS]

    cost_matrix = np.full((len(top_48), MAX_BLOCKS), 9999)

    def block_to_time(b):
        h, m = divmod(b * 30, 60)
        return f"{h:02d}:{m:02d}"

    for i, sub in enumerate(top_48):
        for start, end in sub["availability"]:
            if start == end:
                if 0 <= start < MAX_BLOCKS:
                    cost_matrix[i, start] = -sub["speedups"]
            else:
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
            "availability_str": availability_str
        })

    no_asignados = []
    for i, sub in enumerate(top_48):
        if i not in asignados_idx:
            availability_str = ", ".join([
                f"{block_to_time(start)}–{block_to_time(end)}"
                for (start, end) in sub["availability"]
            ])
            no_asignados.append({
                "nickname": sub["nickname"],
                "ingame_id": sub.get("ingame_id"),
                "alliance": sub["alliance"],
                "speedups": int(sub["speedups"]),
                "availability_str": availability_str
            })

    return sorted(results, key=lambda x: x["hour_block"]), no_asignados


def run_assignment_for_group_day(db: Session, group_day_id: int, cupos=None):
    """
    Ejecuta la asignación de citas para un día específico del grupo.
    Admite cupos por alianza si se pasan.
    """
    from app.models import UserSubmission

    submissions = db.query(UserSubmission).filter(UserSubmission.group_day_id == group_day_id).all()
    if not submissions:
        return [], [], {}

    def block_to_time(b):
        h, m = divmod(b * 30, 60)
        return f"{h:02d}:{m:02d}"

    formatted = []
    for sub in submissions:
        blocks = []
        for slot in sub.availability:
            start_block = slot.start_time.hour * 2 + (1 if slot.start_time.minute >= 30 else 0)
            end_block = slot.end_time.hour * 2 + (1 if slot.end_time.minute >= 30 else 0)
            blocks.append((start_block, end_block))

        availability_str = ", ".join([
            f"{block_to_time(start)}–{block_to_time(end)}"
            for (start, end) in blocks
        ])

        formatted.append({
            "nickname": sub.nickname,
            "ingame_id": sub.ingame_id,
            "speedups": sub.speedups,
            "alliance": sub.alliance.name,
            "availability": blocks,
            "availability_str": availability_str
        })

    top_48, cupos_restantes = seleccionar_top_48(formatted, cupos)
    asignaciones, no_asignados = assign_slots_with_hungarian(top_48)

    return asignaciones, no_asignados, cupos_restantes

