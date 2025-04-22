from fastapi import APIRouter, Request
from app.dependencies import get_templates

router = APIRouter(
    prefix="/public",
    tags=["Public"]
)

# ----------------------------------------
# GET: Public view for searching states
# ----------------------------------------
@router.get("/search")
def search_state(request: Request, code: str = None):
    templates = get_templates(request)
    context = {"request": request}
    if code:
        context["code_found"] = code
    return templates.TemplateResponse("buscar_estado.html", context)
