from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
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
# GET: Mostrar formulario inicial para crear grupo
# ----------------------------------
@router.get("/create")
def show_create_group_form(request: Request):
    templates = get_templates(request)
    request.session["allow_group_creation"] = True
    return templates.TemplateResponse("crear_grupo.html", {
        "request": request
    })


# ----------------------------------
# GET: Mostrar plantilla para configuración al crear grupo
# ----------------------------------
@router.get("/settings")
def group_settings_from_creation(
    request: Request,
    state_number: str,
    group_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)

    # 🚫 Bloqueo de acceso si no viene del flujo correcto
    if not request.session.get("allow_group_creation"):
        return RedirectResponse("/", status_code=303)

    # ✅ Eliminar la bandera para que no pueda reutilizarla
    request.session.pop("allow_group_creation", None)

    # Validar si el código ya existe
    existing = db.query(models.Group).filter(models.Group.group_code == group_code).first()
    if existing:
        return templates.TemplateResponse("crear_grupo.html", {
            "request": request,
            "error": "⚠️ Este código ya está en uso.",
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
            "error": "⚠️ Este código ya está en uso.",
            "state_number": state_number,
            "group_code": group_code
        })

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
                "group_code": group_code,
                "error": f"Nombre de alianza {i} inválido"
            })
        db.add(models.Alliance(group_id=new_group.id, name=name))

    db.add(models.Alliance(group_id=new_group.id, name="Otra"))

    for i in range(1, num_days + 1):
        day_name = form.get(f"day_{i}", "").strip()
        if not validar_nombre_dia(day_name):
            return templates.TemplateResponse("grupo_settings_create.html", {
                "request": request,
                "state_number": state_number,
                "group_code": group_code,
                "error": f"Nombre del día {i} inválido"
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
    alliances_serializable = [{"id": a.id, "name": a.name} for a in group.alliances if a.name != "Otra"]
    days_serializable = [{"id": d.id, "name": d.name} for d in group.days]
    if not group:
        return RedirectResponse("/dashboard")

    is_creator = (group.creator_id == current_user.id)

    return templates.TemplateResponse("grupo_home.html", {
        "request": request,
        "group": group,
        "is_creator": is_creator,
        "alliances_serializable": alliances_serializable,
        "days_serializable": days_serializable
    })


# ----------------------------------
# GET: Configuración editable del grupo desde grupo_home
# ----------------------------------
@router.get("/settings/{group_code}")
def group_settings_edit(
    group_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)
    group = db.query(models.Group).filter(models.Group.group_code == group_code).first()

    if not group or group.creator_id != current_user.id:
        return RedirectResponse("/dashboard")

    # Convertir objetos SQLAlchemy a estructuras nativas serializables
    alliances_serializable = [{"id": a.id, "name": a.name} for a in group.alliances if a.name != "Otra"]
    days_serializable = [{"id": d.id, "name": d.name} for d in group.days]

    return templates.TemplateResponse("grupo_settings_edit.html", {
        "request": request,
        "group": group,
        "alliances_serializable": alliances_serializable,
        "days_serializable": days_serializable
    })



# ----------------------------------
# POST: Actualizar configuración de un grupo ya existente
# ----------------------------------
@router.post("/update-settings/{group_code}")
async def update_group_settings(
    group_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)

    group = db.query(models.Group).filter(models.Group.group_code == group_code).first()
    if not group or group.creator_id != current_user.id:
        return RedirectResponse("/dashboard")

    form = await request.form()
    num_alliances = int(form.get("num_alliances", 0))
    num_days = int(form.get("num_days", 0))

    if num_alliances < 1 or num_days < 1:
        return templates.TemplateResponse("grupo_settings_edit.html", {
            "request": request,
            "group": group,
            "error": "Debe ingresar al menos una alianza y un día."
        })

    alliance_regex = re.compile(r"^[A-Za-z0-9]{3}$")

    def validar_nombre_dia(nombre: str) -> bool:
        if len(nombre) > 20 or len(nombre.strip()) == 0:
            return False
        for char in nombre:
            if not (char.isalnum() or char.isspace()):
                return False
        return True

    db.query(models.Alliance).filter(models.Alliance.group_id == group.id).delete()
    db.query(models.GroupDay).filter(models.GroupDay.group_id == group.id).delete()
    db.commit()

    for i in range(1, num_alliances + 1):
        name = form.get(f"alliance_{i}", "").strip()
        if not alliance_regex.fullmatch(name):
            return templates.TemplateResponse("grupo_settings_edit.html", {
                "request": request,
                "group": group,
                "error": f"Nombre de alianza {i} inválido"
            })
        db.add(models.Alliance(group_id=group.id, name=name))

    db.add(models.Alliance(group_id=group.id, name="Otra"))

    for i in range(1, num_days + 1):
        day_name = form.get(f"day_{i}", "").strip()
        if not validar_nombre_dia(day_name):
            return templates.TemplateResponse("grupo_settings_edit.html", {
                "request": request,
                "group": group,
                "error": f"Nombre del día {i} inválido"
            })
        db.add(models.GroupDay(group_id=group.id, name=day_name))

    db.commit()

    return RedirectResponse(f"/groups/view/{group.group_code}", status_code=303)






@router.post("/update-settings/{group_code}")
async def update_group_settings(
    group_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)

    group = db.query(models.Group).filter(models.Group.group_code == group_code).first()
    if not group or group.creator_id != current_user.id:
        return RedirectResponse("/dashboard")

    form = await request.form()
    num_alliances = int(form.get("num_alliances", 0))
    num_days = int(form.get("num_days", 0))

    # Validaciones mínimas
    if num_alliances < 1 or num_days < 1:
        return templates.TemplateResponse("grupo_settings_edit.html", {
            "request": request,
            "group": group,
            "error": "Debe ingresar al menos una alianza y un día."
        })

    # Borrar alianzas y días antiguos
    db.query(models.Alliance).filter(models.Alliance.group_id == group.id).delete()
    db.query(models.GroupDay).filter(models.GroupDay.group_id == group.id).delete()
    db.commit()

    # Alianzas personalizadas
    for i in range(1, num_alliances + 1):
        name = form.get(f"alliance_{i}", "").strip()
        if len(name) != 3:
            return templates.TemplateResponse("grupo_settings_edit.html", {
                "request": request,
                "group": group,
                "error": f"Nombre de alianza {i} inválido"
            })
        db.add(models.Alliance(group_id=group.id, name=name))

    # Alianza adicional 'Otra'
    db.add(models.Alliance(group_id=group.id, name="Otra"))

    # Días personalizados
    for i in range(1, num_days + 1):
        day_name = form.get(f"day_{i}", "").strip()
        if not day_name:
            return templates.TemplateResponse("grupo_settings_edit.html", {
                "request": request,
                "group": group,
                "error": f"Nombre del día {i} inválido"
            })
        db.add(models.GroupDay(group_id=group.id, name=day_name))

    db.commit()

    return RedirectResponse(f"/groups/view/{group.group_code}", status_code=303)
