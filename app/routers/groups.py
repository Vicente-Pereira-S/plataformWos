from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.utils_auth import get_current_user
from app.dependencies import get_templates

router = APIRouter(
    prefix="/groups",
    tags=["Groups"]
)

# ----------------------------------
# GET: Show group creation form
# ----------------------------------
@router.get("/create")
def show_create_group_form(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("crear_grupo.html", {
        "request": request
    })


# ----------------------------------
# POST: Process group creation
# ----------------------------------
@router.post("/create-group")
def create_group(
    request: Request,
    state_number: str = Form(...),
    group_code: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)

    # Check if group code already exists
    existing_group = db.query(models.Group).filter(models.Group.group_code == group_code).first()
    if existing_group:
        return templates.TemplateResponse("crear_grupo.html", {
            "request": request,
            "error": "⚠️ This code is already in use. Please choose another.",
            "state_number": state_number,
            "group_code": group_code
        })

    # Create the group
    new_group = models.Group(
        state_number=state_number,
        group_code=group_code,
        creator_id=current_user.id
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # Add the current user as admin in GroupMember
    membership = models.GroupMember(
        user_id=current_user.id,
        group_id=new_group.id,
        role="admin"
    )
    db.add(membership)
    db.commit()

    return templates.TemplateResponse("grupo_creado.html", {
        "request": request,
        "group_code": new_group.group_code,
        "state_number": new_group.state_number
    })


# ----------------------------------
# GET: Show groups where current user belongs
# ----------------------------------
@router.get("/my-groups")
def view_my_groups(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    templates = get_templates(request)

    # Obtener todos los grupos a los que pertenece el usuario
    memberships = db.query(models.GroupMember).filter_by(user_id=current_user.id).all()

    # Separar en dos listas: admin y miembro
    admin_groups = [m.group for m in memberships if m.role == "admin"]
    member_groups = [m.group for m in memberships if m.role != "admin"]

    return templates.TemplateResponse("mis_grupos.html", {
        "request": request,
        "admin_groups": admin_groups,
        "member_groups": member_groups
    })

