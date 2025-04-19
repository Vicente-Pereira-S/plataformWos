from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine
from app.routers import groups, public, auth
from app.dependencies import get_templates

from jinja2 import Environment, FileSystemLoader, select_autoescape
import gettext
import os


app = FastAPI()

# Inicializar base de datos (en producción usar Alembic)
Base.metadata.create_all(bind=engine)

# Archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Middleware de sesión
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    raise RuntimeError("SESSION_SECRET_KEY no está definida en el entorno")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lista de idiomas permitidos
AVAILABLE_LANGS = {"es", "en", "ko", "tr"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    templates = get_templates(request)
    access_token = request.cookies.get("access_token")
    is_logged_in = access_token is not None

    return templates.TemplateResponse("home.html", {
        "request": request,
        "is_logged_in": is_logged_in
    })



@app.get("/auth/login", response_class=HTMLResponse)
async def show_login_form(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/auth/register", response_class=HTMLResponse)
async def show_register_form(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/set-language/{lang_code}")
async def set_language(lang_code: str, request: Request):
    if lang_code not in AVAILABLE_LANGS:
        lang_code = "es"
    response = RedirectResponse(url=request.headers.get("referer", "/"))
    response.set_cookie(key="preferred_lang", value=lang_code)
    return response

# Routers del sistema
app.include_router(groups.router)
app.include_router(public.router)
app.include_router(auth.router)
