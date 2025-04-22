from fastapi.templating import Jinja2Templates
from starlette_babel import get_locale
from starlette_babel import gettext_lazy as _

templates = Jinja2Templates(directory="app/templates")

def get_templates(request):
    templates.env.globals["_"] = _
    templates.env.globals["get_locale"] = get_locale
    templates.env.globals["is_logged_in"] = getattr(request.state, "is_logged_in", False)
    return templates
