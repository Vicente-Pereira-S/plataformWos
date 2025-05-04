from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app import models
import os
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
