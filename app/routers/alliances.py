from fastapi import APIRouter, Request
from app.dependencies import get_templates

router = APIRouter(
    prefix="/alliances",
    tags=["Alliances"]
)

# ----------------------------------------
# Ruta base para futuro desarrollo
# ----------------------------------------
@router.get("/")
def alliances_home(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("dashboard.html", {"request": request})
