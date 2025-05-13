from app.database import SessionLocal
from app.utils import run_assignment_for_group_day
from app.models import GroupDay

# Cargar DB
db = SessionLocal()

# Busca el group_day_id que quieres probar (puedes cambiar el número o buscar por nombre)
group_day = db.query(GroupDay).filter(GroupDay.name == "troopas").first()

if not group_day:
    print("❌ No se encontró el día del grupo")
else:
    result = run_assignment_for_group_day(db, group_day.id)
    print(f"✅ Asignaciones para el día: {group_day.name}\n")

    for r in result:
        print(f"{r['hour_block']:02d} - {r['nickname']} ({r['speedups']} speedups) [{r['alliance']}]")
        print(f"    Disponibilidad: {r['availability_str']}")
