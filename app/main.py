from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.routers import groups, public, auth
from app.dependencies import get_templates, inject_login_context
from app.utils_auth import get_current_user_optional, ocultar_email
from app import models

import os

app = FastAPI()

# Inicializar base de datos
Base.metadata.create_all(bind=engine)

# Archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Middleware de sesión
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    raise RuntimeError("SESSION_SECRET_KEY no está definida en el entorno")

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Idiomas disponibles
AVAILABLE_LANGS = {"es", "en", "ko", "tr"}


# ------------------- RUTAS PRINCIPALES -------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user_id = get_current_user_optional(request)
    if user_id:
        return RedirectResponse(url="/dashboard")

    templates = get_templates(request)
    inject_login_context(request, templates)
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/auth/login", response_class=HTMLResponse)
async def show_login_form(request: Request):
    templates = get_templates(request)
    inject_login_context(request, templates)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/auth/register", response_class=HTMLResponse)
async def show_register_form(request: Request):
    templates = get_templates(request)
    inject_login_context(request, templates)
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = ""):
    templates = get_templates(request)
    inject_login_context(request, templates)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": username
    })


@app.get("/buscar-estado", response_class=HTMLResponse)
async def buscar_estado(request: Request, codigo: str = None):
    templates = get_templates(request)
    inject_login_context(request, templates)
    context = {"request": request}
    if codigo:
        context["codigo_encontrado"] = codigo
    return templates.TemplateResponse("buscar_estado.html", context)


@app.get("/set-language/{lang_code}")
async def set_language(lang_code: str, request: Request):
    if lang_code not in AVAILABLE_LANGS:
        lang_code = "es"
    response = RedirectResponse(url=request.headers.get("referer", "/"))
    response.set_cookie(key="preferred_lang", value=lang_code)
    return response


# ------------------- RECUPERACIÓN DE CONTRASEÑA -------------------

@app.get("/auth/recuperar", response_class=HTMLResponse)
async def show_recovery_form(request: Request):
    templates = get_templates(request)
    inject_login_context(request, templates)
    return templates.TemplateResponse("recuperar_contraseña.html", {
        "request": request
    })


@app.post("/auth/recuperar", response_class=HTMLResponse)
async def process_recovery_form(
    request: Request,
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    templates = get_templates(request)
    inject_login_context(request, templates)

    user = db.query(models.User).filter(models.User.username == username).first()

    if user and user.email:
        correo_oculto = ocultar_email(user.email)
        return templates.TemplateResponse("confirmar_recuperacion.html", {
            "request": request,
            "username": username,
            "correo_oculto": correo_oculto
        })
    else:
        return templates.TemplateResponse("sin_correo.html", {
            "request": request,
            "username": username
        })


# ------------------- INCLUYE LOS ROUTERS -------------------

app.include_router(groups.router)
app.include_router(public.router)
app.include_router(auth.router)
