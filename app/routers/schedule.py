from fastapi import APIRouter, Request
from app.dependencies import get_templates

router = APIRouter(
    prefix="/schedule",
    tags=["Schedule"]
)

# ----------------------------------------
# Ruta base para desarrollo futuro
# ----------------------------------------
@router.get("/")
def show_schedule_dashboard(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("dashboard.html", {"request": request})
