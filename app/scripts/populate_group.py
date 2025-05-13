import random
from datetime import time
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models

def generate_random_slot():
    start_hour = random.randint(0, 22)
    start_minute = random.choice([0, 30])
    end_hour = start_hour
    end_minute = 30 if start_minute == 0 else 0
    end_hour += 1 if start_minute == 30 else 0
    return time(start_hour, start_minute), time(end_hour, end_minute)

def populate_group(group_code: str, num_users: int = 60):
    db: Session = SessionLocal()
    group = db.query(models.Group).filter_by(group_code=group_code).first()

    if not group:
        print(f"Grupo con código '{group_code}' no encontrado.")
        return

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
            db.flush()  # Para obtener submission.id

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
    print(f"✅ Grupo '{group_code}' poblado con éxito con {num_users} usuarios por día.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("❗Uso: python3 -m app.scripts.populate_group <codigo_grupo>")
    else:
        populate_group(sys.argv[1])
