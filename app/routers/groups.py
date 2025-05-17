from fastapi import APIRouter, Body, HTTPException, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

import re

from app.database import get_db
from app import models
from app.utils_auth import get_current_user
from app.utils import run_assignment_for_group_day
from app.dependencies import get_templates

router = APIRouter(
    prefix="/groups",
    tags=["Groups"]
)

def validar_nombre_dia(nombre: str) -> bool:
    if len(nombre) > 20 or len(nombre.strip()) == 0:
        return False
    for char in nombre:
        if not (char.isalnum() or char.isspace()):
            return False
    return True


# ----------------------------------
# Concepto	Qué hace
# Depends	Llama funciones automáticamente para ti.
# get_db	Crea conexión segura a la base de datos.
# Session	Objeto para consultar/guardar en base de datos.
# (request: Request, db: Session, ...)	Define todos los inputs del endpoint.
# db.query(...).first()	Devuelve un objeto si existe, o None si no.
# TemplateResponse(..., {...})	Envía variables a tu HTML de manera interna.
# ----------------------------------


# GET: Mostrar formulario inicial para crear grupo
# Solo es llamado desde dashboard.html
# ----------------------------------
@router.get("/create")
def show_create_group_form(request: Request):
    templates = get_templates(request)                  # Prepara el motor de plantillas para renderizar HTML.
    request.session["allow_group_creation"] = True
    return templates.TemplateResponse("crear_grupo.html", {
        "request": request
    })


# ----------------------------------
# GET: Mostrar plantilla para configuración al crear grupo

# current_user: models.User = Depends(get_current_user) -> 
# tecnicamente me devuelve un usuario, pero si no hace match
# con un usuario logueado en la pagina, devuelve un 401, y sirve como seguridad para que no vean la pagina
# ----------------------------------
@router.get("/settings")
def group_settings_from_creation(
    request: Request,
    state_number: str,          # Informacion la trae la URL y la guardo de esta forma
    group_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)

    # Bloqueo de acceso si no viene del flujo correcto
    if not request.session.get("allow_group_creation"):
        return RedirectResponse("/", status_code=303)

    # Eliminar la bandera para que no pueda reutilizarla
    request.session.pop("allow_group_creation", None)

    # Validar si el código ya existe
    existing = db.query(models.Group).filter(models.Group.group_code == group_code).first()
    if existing:
        return templates.TemplateResponse("crear_grupo.html", {
            "request": request,
            "error": "flag code error",
            "state_number": state_number,
            "group_code": group_code
        })

    return templates.TemplateResponse("grupo_settings_create.html", {
        "request": request,
        "state_number": state_number,
        "group_code": group_code
    })



# ----------------------------------
# POST: Crear grupo y guardar configuración inicial
# ----------------------------------

# ALERTA! Cuando analice JS, preguntar a chatGPT si ahcen lo mismo con regex,a bmos analizan y envian un mensaje de error,v er el FOR
# creo que es por doble autenticacion si desactivan JS en navegador.
@router.post("/create-group")
async def create_group_post(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)

    form = await request.form()
    state_number = form.get("state_number", "")
    group_code = form.get("group_code", "")
    num_alliances = int(form.get("num_alliances", 0))
    num_days = int(form.get("num_days", 0))

    existing = db.query(models.Group).filter(models.Group.group_code == group_code).first()
    if existing:
        return templates.TemplateResponse("crear_grupo.html", {
            "request": request,
            "error": "flag code error",
            "state_number": state_number,
            "group_code": group_code
        })

    # Regex (expresión regular) para validar que los nombres de alianzas:
    # Tengan exactamente 3 caracteres. Sean solo letras o números.
    alliance_regex = re.compile(r"^[A-Za-z0-9]{3}$") 

    new_group = models.Group(
        state_number=state_number,
        group_code=group_code,
        creator_id=current_user.id
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    db.add(models.GroupMember(user_id=current_user.id, group_id=new_group.id))
    db.commit()

    for i in range(1, num_alliances + 1):
        name = form.get(f"alliance_{i}", "").strip()
        if not alliance_regex.fullmatch(name):
            return templates.TemplateResponse("grupo_settings_create.html", {
                "request": request,
                "state_number": state_number,
                "group_code": group_code
            })
        db.add(models.Alliance(group_id=new_group.id, name=name))

    # Seguridad por si fuerzan el html desde el navegador
    for i in range(1, num_days + 1):
        day_name = form.get(f"day_{i}", "").strip()
        if not validar_nombre_dia(day_name):
            return templates.TemplateResponse("grupo_settings_create.html", {
                "request": request,
                "state_number": state_number,
                "group_code": group_code
            })
        db.add(models.GroupDay(group_id=new_group.id, name=day_name))

    db.commit()

    return templates.TemplateResponse("grupo_creado.html", {
        "request": request,
        "group_code": new_group.group_code,
        "state_number": new_group.state_number
    })



# ----------------------------------
# GET: Ver todos los grupos del usuario
# ----------------------------------
@router.get("/my-groups")
def view_my_groups(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)
    memberships = db.query(models.GroupMember).filter_by(user_id=current_user.id).all()
    groups = [membership.group for membership in memberships]

    return templates.TemplateResponse("mis_grupos.html", {
        "request": request,
        "groups": groups
    })


# ----------------------------------
# GET: Vista del grupo
# ----------------------------------
@router.get("/view/{group_code}")
def view_group(
    group_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)

    # Buscar grupo
    group = db.query(models.Group).filter(models.Group.group_code == group_code).first()

    if not group:
        return templates.TemplateResponse("grupo_no_encontrado.html", {
            "request": request
        })

    # Estructuras auxiliares para frontend
    alliances_serializable = [{"id": a.id, "name": a.name} for a in group.alliances]
    days_serializable = [{"id": d.id, "name": d.name} for d in group.days]

    is_creator = (group.creator_id == current_user.id)

    # Cargar asignaciones por día (GroupAssignment)
    assignments_by_day = {
        d.id: db.query(models.GroupAssignment).filter_by(group_day_id=d.id).all()
        for d in group.days
    }

    # Cargar no asignados por día (GroupUnassigned)
    no_asignados_by_day = {
        d.id: db.query(models.GroupUnassigned).filter_by(group_day_id=d.id).all()
        for d in group.days
    }

    return templates.TemplateResponse("grupo_home.html", {
        "request": request,
        "group": group,
        "current_user": current_user,
        "is_creator": is_creator,
        "alliances_serializable": alliances_serializable,
        "days_serializable": days_serializable,
        "assignments_by_day": assignments_by_day,
        "no_asignados_by_day": no_asignados_by_day
    })



# ----------------------------------
# POST: Actualizar configuración de un grupo ya existente (MODAL lo usa)
# ----------------------------------
@router.post("/update-settings/{group_code}")
async def update_group_settings(
    group_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)

    # Buscar grupo
    group = db.query(models.Group).filter(models.Group.group_code == group_code).first()
    if not group or group.creator_id != current_user.id:
        return RedirectResponse("/dashboard")

    # Leer formulario
    form = await request.form()
    num_alliances = int(form.get("num_alliances", 0))
    num_days = int(form.get("num_days", 0))

    # Validar mínimo
    if num_alliances < 1 or num_days < 1:
        return RedirectResponse(f"/groups/view/{group.group_code}")

    # Borrar datos anteriores
    db.query(models.Alliance).filter(models.Alliance.group_id == group.id).delete()
    db.query(models.GroupDay).filter(models.GroupDay.group_id == group.id).delete()
    db.commit()

    # Validar y guardar nuevas alianzas
    alliance_regex = re.compile(r"^[A-Za-z0-9]{3}$")
    for i in range(1, num_alliances + 1):
        name = form.get(f"alliance_{i}", "").strip()
        if not alliance_regex.fullmatch(name):
            return RedirectResponse(f"/groups/view/{group.group_code}")
        db.add(models.Alliance(group_id=group.id, name=name))


    # Validar y guardar nuevos días
    for i in range(1, num_days + 1):
        day_name = form.get(f"day_{i}", "").strip()
        if len(day_name) == 0 or len(day_name) > 20 or not all(c.isalnum() or c.isspace() for c in day_name):
            return RedirectResponse(f"/groups/view/{group.group_code}")
        db.add(models.GroupDay(group_id=group.id, name=day_name))

    db.commit()

    # Redirigir de vuelta al grupo
    return RedirectResponse(f"/groups/view/{group.group_code}", status_code=303)






@router.get("/members/{group_code}")
def get_group_members(group_code: str, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter_by(group_code=group_code).first()
    if not group:
        raise HTTPException(status_code=404)
    return {
        "members": [{"id": m.user.id, "username": m.user.username} for m in group.members]
    }




@router.get("/search-user-by-id/{user_id}")
def search_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return {"error": "Usuario no encontrado"}
    return {"id": user.id, "username": user.username}





@router.post("/save-members/{group_code}")
def save_members(
    group_code: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    group = db.query(models.Group).filter_by(group_code=group_code).first()
    if not group or group.creator_id != current_user.id:
        raise HTTPException(status_code=403)
    
    nuevos_ids = list(set(payload.get("user_ids", [])))
    if group.creator_id not in nuevos_ids:
        nuevos_ids.append(group.creator_id)

    db.query(models.GroupMember).filter_by(group_id=group.id).delete()
    for uid in nuevos_ids:
        db.add(models.GroupMember(group_id=group.id, user_id=uid))
    db.commit()
    return {"success": True}




@router.post("/leave")
def leave_group(
    request: Request,
    group_code: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    group = db.query(models.Group).filter_by(group_code=group_code).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")

    # Verificar si el usuario es miembro
    member = db.query(models.GroupMember).filter_by(group_id=group.id, user_id=current_user.id).first()
    if not member:
        raise HTTPException(status_code=403, detail="No eres miembro de este grupo")

    # Si es el creador, validamos cantidad de miembros
    if group.creator_id == current_user.id:
        total_miembros = db.query(models.GroupMember).filter_by(group_id=group.id).count()
        if total_miembros > 1:
            raise HTTPException(status_code=403, detail="Eres el creador. Transfiere el grupo antes de salir.")

        # Es el único miembro → se borra el grupo entero
        db.delete(group)
        db.commit()
        return RedirectResponse("/groups/my-groups", status_code=303)

    # Si no es el creador, simplemente se elimina del grupo
    db.delete(member)
    db.commit()
    return RedirectResponse("/groups/my-groups", status_code=303)






class TransferRequest(BaseModel):
    group_code: str
    new_owner_id: int

@router.post("/transfer")
def transfer_group_ownership(
    data: TransferRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Buscar grupo
    group = db.query(models.Group).filter_by(group_code=data.group_code).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")

    # Verificar que quien solicita sea el creador
    if group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para transferir este grupo")

    # Verificar que el nuevo dueño esté en la lista de miembros
    miembro = db.query(models.GroupMember).filter_by(group_id=group.id, user_id=data.new_owner_id).first()
    if not miembro:
        raise HTTPException(status_code=400, detail="El nuevo dueño no es miembro del grupo")

    # Actualizar el grupo
    group.creator_id = data.new_owner_id
    db.commit()

    return {"success": True}


@router.post("/delete")
def delete_group(
    request: Request,
    group_code: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Buscar el grupo
    group = db.query(models.Group).filter_by(group_code=group_code).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")

    # Verificar que el usuario actual sea el creador
    if group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este grupo")

    # Eliminar el grupo (relaciones con cascade eliminarán alianzas, días y miembros)
    db.delete(group)
    db.commit()

    return RedirectResponse("/groups/my-groups", status_code=303)




# Página separada para ver todos los postulantes
@router.get("/postulaciones/{day_id}", response_class=HTMLResponse)
def ver_postulaciones_dia(
    day_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)

    # Buscar el día
    day = (
    db.query(models.GroupDay)
    .join(models.Group)
    .filter(models.GroupDay.id == day_id, models.GroupDay.group_id == models.Group.id)
    .first()
)

    if not day:
        return templates.TemplateResponse("grupo_no_encontrado.html", {"request": request})

    group = day.group

    # Verificar que el usuario sea miembro del grupo
    es_miembro = db.query(models.GroupMember).filter_by(
        group_id=group.id,
        user_id=current_user.id
    ).first()

    if not es_miembro:
        raise HTTPException(status_code=403, detail="No autorizado")

    # Obtener todas las alianzas disponibles (para mostrar en el select en modo edición)
    alliances = db.query(models.Alliance).filter(models.Alliance.group_id == group.id).all()

    return templates.TemplateResponse("ver_postulaciones.html", {
        "request": request,
        "day": day,
        "alliances": alliances,
        "current_user": current_user
    })


# Endpoint AJAX que ejecuta el algoritmo y devuelve los resultados
@router.post("/asignar/{day_id}")
def ejecutar_asignacion(
    day_id: int,
    db: Session = Depends(get_db),
    body: dict = Body(default={})
):
    try:
        # Extraer "cupos" desde el cuerpo del request
        raw_cupos = body.get("cupos", {})
        cupos = {}

        if raw_cupos and isinstance(raw_cupos, dict):
            cupos = {
                str(k): int(v)
                for k, v in raw_cupos.items()
                if isinstance(k, str) and isinstance(v, int) and v >= 0
            }

        # Ejecutar el algoritmo con los cupos recibidos
        asignaciones, no_asignados, restantes = run_assignment_for_group_day(db, day_id, cupos=cupos)


        # Preparar estructura segura para frontend
        safe_asignaciones = [
            {
                "hour_block": int(a["hour_block"]),
                "nickname": a["nickname"],
                "ingame_id": a["ingame_id"],
                "alliance": a["alliance"],
                "speedups": int(a["speedups"]),
                "availability_str": a["availability_str"],
            }
            for a in asignaciones
        ]

        safe_no_asignados = [
            {
                "nickname": u["nickname"],
                "ingame_id": u["ingame_id"],
                "alliance": u["alliance"],
                "speedups": int(u["speedups"]),
                "availability_str": u["availability_str"]
            }
            for u in no_asignados
        ]

        return {
            "success": True,
            "data": {
                "assignments": safe_asignaciones,
                "unassigned": safe_no_asignados,
                "remaining": restantes
            }
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "success": False,
            "error": str(e)
        })




from fastapi import Form

@router.post("/delete-submissions")
def eliminar_postulaciones(
    request: Request,
    day_id: int = Form(...),
    submission_ids: str = Form(...),  # Recibe como string
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Convertir string "59,6" -> [59, 6]
    try:
        ids = [int(x.strip()) for x in submission_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato inválido de IDs")

    # Verificar existencia del día
    day = (
    db.query(models.GroupDay)
    .join(models.Group)
    .filter(models.GroupDay.id == day_id, models.GroupDay.group_id == models.Group.id)
    .first()
)

    if not day:
        raise HTTPException(status_code=404, detail="Día no encontrado")

    # Verificar que el usuario es miembro del grupo
    miembro = db.query(models.GroupMember).filter_by(
        group_id=day.group.id,
        user_id=current_user.id
    ).first()
    if not miembro:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")

    # Eliminar las postulaciones
    for sub_id in ids:
        sub = db.query(models.UserSubmission).filter_by(id=sub_id, group_day_id=day.id).first()
        if sub:
            db.delete(sub)

    db.commit()
    return RedirectResponse(f"/groups/postulaciones/{day.id}", status_code=303)





@router.post("/guardar-asignaciones/{day_id}")
def guardar_asignaciones(
    day_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    from app.models import GroupDay, GroupAssignment, GroupUnassigned

    group_day = db.query(GroupDay).filter(GroupDay.id == day_id).first()
    if not group_day or group_day.group.creator_id != current_user.id:
        return JSONResponse({"success": False, "error": "No autorizado"}, status_code=403)

    sobrescribir = data.get("sobrescribir", False)
    asignaciones = data.get("asignaciones", [])
    no_asignados = data.get("no_asignados", [])

    if sobrescribir:
        db.query(GroupAssignment).filter_by(group_day_id=day_id).delete()
        db.query(GroupUnassigned).filter_by(group_day_id=day_id).delete()

    # Guardar asignaciones
    for a in asignaciones:
        if a.get("nickname") is None:
            # Bloque vacío
            new_assignment = GroupAssignment(
                group_day_id=day_id,
                hour_block=a["hour_block"],
                nickname=None,
                ingame_id=None,
                alliance="---",
                speedups=0,
                availability_str=""
            )
        else:
            new_assignment = GroupAssignment(
                group_day_id=day_id,
                hour_block=a["hour_block"],
                nickname=a["nickname"],
                ingame_id=a.get("ingame_id"),
                alliance=a["alliance"],
                speedups=a["speedups"],
                availability_str=a["availability_str"]
            )
        db.add(new_assignment)

    # Guardar no asignados
    for u in no_asignados:
        nuevo = GroupUnassigned(
            group_day_id=day_id,
            nickname=u["nickname"],
            ingame_id=u.get("ingame_id"),
            alliance=u["alliance"],
            speedups=u["speedups"],
            availability_str=u["availability_str"]
        )
        db.add(nuevo)

    db.commit()
    return {"success": True}
