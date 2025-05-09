from fastapi import APIRouter, Body, HTTPException, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import re

from app.database import get_db
from app import models
from app.utils_auth import get_current_user
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

    db.add(models.Alliance(group_id=new_group.id, name="Otra"))

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
    
    
    # Convertir objetos SQLAlchemy a estructuras nativas serializables
    group = db.query(models.Group).filter(models.Group.group_code == group_code).first()
    
    if not group:
        return templates.TemplateResponse("grupo_no_encontrado.html", {
        "request": request
    })
    
    alliances_serializable = [{"id": a.id, "name": a.name} for a in group.alliances if a.name != "Otra"]
    days_serializable = [{"id": d.id, "name": d.name} for d in group.days]
    

    is_creator = (group.creator_id == current_user.id)

    return templates.TemplateResponse("grupo_home.html", {
        "request": request,
        "group": group,
        "current_user": current_user,
        "is_creator": is_creator,       # Boolean 
        "alliances_serializable": alliances_serializable,
        "days_serializable": days_serializable
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

    # Siempre agregar "Otra"
    db.add(models.Alliance(group_id=group.id, name="Otra"))

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
