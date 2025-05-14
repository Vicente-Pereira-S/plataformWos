from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.dependencies import get_templates
from app.database import get_db
from app import models
from datetime import datetime

router = APIRouter(
    prefix="/public",
    tags=["Public"]
)

@router.get("/search-state", response_class=HTMLResponse)
async def search_state(request: Request, group_code: str = None):
    templates = get_templates(request)
    context = {"request": request}
    if group_code:
        context["code_found"] = group_code
    return templates.TemplateResponse("buscar_estado.html", context)

# Ruta AJAX para búsqueda sin recarga
@router.get("/search-state-ajax")
def search_state_ajax(code: str, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.group_code == code).first()
    if group:
        return {"success": True, "state_number": group.state_number}
    return {"success": False}


# Muestra el formulario para enviar disponibilidad (HTML)
@router.get("/enviar-disponibilidad/{group_code}", response_class=HTMLResponse)
def show_submission_form(group_code: str, request: Request, db: Session = Depends(get_db)):
    templates = get_templates(request)
    group = db.query(models.Group).filter(models.Group.group_code == group_code).first()

    if not group:
        return templates.TemplateResponse("grupo_no_encontrado.html", {"request": request})

    alliances = db.query(models.Alliance).filter(models.Alliance.group_id == group.id).all()
    alliances_serializable = [{"id": a.id, "name": a.name} for a in alliances]

    # Días del grupo
    days = db.query(models.GroupDay).filter(models.GroupDay.group_id == group.id).all()
    days_serializable = [{"id": d.id, "name": d.name} for d in days]

    return templates.TemplateResponse("enviar_disponibilidad.html", {
        "request": request,
        "group": group,
        "alliances": alliances_serializable,
        "days": days_serializable
    })


# ✅ Recibe los datos enviados desde el formulario (POST)
@router.post("/submit-availability")
async def submit_availability(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    try:
        nickname = data["nickname"]
        ingame_id = data.get("ingame_id")
        alliance_id = int(data["alliance_id"])
        submissions = data["submissions"]

        if not nickname or not submissions:
            raise HTTPException(status_code=400, detail="Datos incompletos")

        for s in submissions:
            group_day_id = int(s["group_day_id"])
            speedups = int(s["speedups"])
            intervals = s["intervals"]

            # Crear instancia principal del envío
            user_submission = models.UserSubmission(
                nickname=nickname,
                ingame_id=ingame_id,
                alliance_id=alliance_id,
                group_day_id=group_day_id,
                speedups=speedups
            )
            db.add(user_submission)
            db.flush()  # Para obtener user_submission.id

            for interval in intervals:
                # ⚠️ Conversión de string a datetime.time
                start_time = datetime.strptime(interval["start"], "%H:%M").time()
                end_time = datetime.strptime(interval["end"], "%H:%M").time()

                slot = models.AvailabilitySlot(
                    submission_id=user_submission.id,
                    start_time=start_time,
                    end_time=end_time
                )
                db.add(slot)

        db.commit()
        return {"success": True}

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})