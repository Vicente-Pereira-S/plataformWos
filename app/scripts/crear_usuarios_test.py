from datetime import datetime, timedelta, timezone
from app.database import SessionLocal
from app import models
from app.utils_auth import hash_password  # si tienes esta función

db = SessionLocal()

# Usuario que será eliminado (inactivo por más de 90 días)
user1 = models.User(
    username="viejo",
    email="viejo@example.com",
    hashed_password=hash_password("1234"),
    last_login=datetime.now(timezone.utc) - timedelta(days=100),
    is_active=True
)

# Usuario activo que NO debe ser eliminado
user2 = models.User(
    username="activo",
    email="activo@example.com",
    hashed_password=hash_password("1234"),
    last_login=datetime.now(timezone.utc),
    is_active=True
)

# Usuario inactivo PERO que es creador de grupo
user3 = models.User(
    username="creador",
    email="creador@example.com",
    hashed_password=hash_password("1234"),
    last_login=datetime.now(timezone.utc) - timedelta(days=100),
    is_active=True
)

# Insertar usuarios
db.add_all([user1, user2, user3])
db.commit()

# Simular que el usuario 3 es creador de grupo
grupo = models.Group(
    state_number=1,
    group_code="TEST",
    creator_id=user3.id
)
db.add(grupo)
db.commit()

# Relación con el grupo
group_member = models.GroupMember(group_id=grupo.id, user_id=user3.id)
db.add(group_member)
db.commit()

db.close()
print("Usuarios de prueba creados.")
