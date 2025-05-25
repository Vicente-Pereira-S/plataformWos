from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_templates
from app.database import get_db
from app import models
from datetime import datetime

router = APIRouter(
    prefix="/public",
    tags=["Public"]
)

@router.get("/search", response_class=HTMLResponse)
def show_group_search_form(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("public_search.html", {"request": request})


@router.get("/schedule/{group_code}", response_class=HTMLResponse)
def public_group_view(group_code: str, request: Request, db: Session = Depends(get_db)):
    templates = get_templates(request)
    group = db.query(models.Group).filter(models.Group.group_code == group_code).first()
    
    if not group:
        return templates.TemplateResponse("grupo_no_encontrado.html", {"request": request})

    assignments_by_day = {
        d.id: db.query(models.GroupAssignment).filter_by(group_day_id=d.id).all()
        for d in group.days
    }

    return templates.TemplateResponse("public_view.html", {
        "request": request,
        "group": group,
        "assignments_by_day": assignments_by_day
    })




# Muestra el formulario para enviar disponibilidad (HTML)
@router.get("/enviar-disponibilidad/{group_code}", response_class=HTMLResponse)
def show_submission_form(group_code: str, request: Request, db: Session = Depends(get_db)):
    templates = get_templates(request)
    group = db.query(models.Group).filter(models.Group.group_code == group_code).first()

    if not group:
        return templates.TemplateResponse("grupo_no_encontrado.html", {"request": request})
    
    if not group.is_open:
        return templates.TemplateResponse("submission_closed.html", {"request": request})

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
        ingame_id_raw = data.get("ingame_id")
        ingame_id = int(ingame_id_raw) if ingame_id_raw not in (None, "", "null") else None
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
    

# Muestra una nueva vista de confirmacion de envio
@router.get("/confirm-submission", response_class=HTMLResponse)
def confirm_submission(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("success_submission.html", {"request": request})
