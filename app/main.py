from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_babel import gettext_lazy as _, LocaleMiddleware
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

# ------------------------------
# Local Modules
# ------------------------------

from app import models
from app.database import Base, engine, get_db
from app.routers import groups, public, auth
from app.dependencies import get_templates
from app.middleware import setup_template_globals
from app.utils_auth import get_current_user_optional, decode_token_from_cookie

# ------------------------------
# App Initialization
# ------------------------------

app = FastAPI()

# Create tables in database if not present
Base.metadata.create_all(bind=engine)

# Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Session Middleware
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    raise RuntimeError("SESSION_SECRET_KEY is not defined in the environment")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

# Babel Locale Middleware (compatible con versión 1.0.3)
app.add_middleware(LocaleMiddleware, default_locale="es")

# Middleware para inyectar globals en plantillas
@app.middleware("http")
async def add_globals_middleware(request: Request, call_next):
    templates = get_templates(request)
    inject_context = setup_template_globals()
    inject_context(request)
    response = await call_next(request)
    return response

# CORS (opcional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# Language Settings
# ------------------------------

AVAILABLE_LANGS = {"es", "en", "ko", "tr"}

@app.get("/set-language/{lang_code}")
async def set_language(lang_code: str, request: Request):
    if lang_code not in AVAILABLE_LANGS:
        lang_code = "es"
    request.session["locale"] = lang_code  # para starlette-babel 1.0.3
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer)

# ------------------------------
# Public Routes
# ------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    templates = get_templates(request)
    user_id = get_current_user_optional(request)
    if user_id:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    templates = get_templates(request)
    user_id = decode_token_from_cookie(request)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user.username,
        "user_id": user.id
    })


# ------------------------------
# Routers
# ------------------------------

app.include_router(groups.router)
app.include_router(public.router)
app.include_router(auth.router)
