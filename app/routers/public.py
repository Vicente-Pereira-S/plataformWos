from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.dependencies import get_templates
from app.database import get_db
from app import models

router = APIRouter(
    prefix="/public",
    tags=["Public"]
)


@router.get("/search-state", response_class=HTMLResponse)
async def search_state(request: Request, code: str = None):
    templates = get_templates(request)
    context = {"request": request}
    if code:
        context["code_found"] = code
    return templates.TemplateResponse("buscar_estado.html", context)

# Ruta AJAX para búsqueda sin recarga
@router.get("/search-state-ajax")
def search_state_ajax(code: str, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.group_code == code).first()
    if group:
        return {"success": True, "state_number": group.state_number}
    return {"success": False}
