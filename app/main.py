from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from starlette.middleware.sessions import SessionMiddleware
from starlette_babel import gettext_lazy as _, LocaleMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy.orm import Session
import os

from dotenv import load_dotenv
load_dotenv()

# ------------------------------
# Local Modules
# ------------------------------

from app import models
from app.database import Base, engine, get_db
from app.routers import groups, public, auth, maintenance
from app.dependencies import get_templates
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


async def add_globals_middleware(request: Request, call_next):
    response = await call_next(request)

    if request.session.pop("session_expired", False):
        response.delete_cookie("access_token")
        response.set_cookie("toast_msg", "Tu sesión ha expirado", max_age=5)

    response.delete_cookie("toast_msg")
    return response


# CORS (opcional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Nuevo middleware para is_logged_in
@app.middleware("http")
async def check_login_status(request: Request, call_next):
    user_id = decode_token_from_cookie(request)
    request.state.is_logged_in = user_id is not None
    response = await call_next(request)
    return response

# ------------------------------
# Language Settings
# ------------------------------

AVAILABLE_LANGS = {"es", "en", "ko", "tr"}

@app.get("/set-language/{lang_code}")
async def set_language(lang_code: str, request: Request):
    if lang_code not in AVAILABLE_LANGS:
        lang_code = "es"
    request.session["locale"] = lang_code 
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer)

# ------------------------------
# Public Routes
# ------------------------------


@app.get("/ping")
def ping():
    return JSONResponse(content={"message": "pong"}, status_code=200)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    templates = get_templates(request)
    user_id = get_current_user_optional(request)
    session_expired = request.session.pop("session_expired", False)
    if user_id:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("home.html", {
        "request": request,
        "session_expired": session_expired
    })

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


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    templates = get_templates(request)

    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    else:
        # para otros errores, puedes dejarlo pasar o personalizar después
        return HTMLResponse(f"<h1>{exc.status_code} Error</h1><p>{exc.detail}</p>", status_code=exc.status_code)


# ------------------------------
# Routers
# ------------------------------

app.include_router(groups.router)
app.include_router(public.router)
app.include_router(auth.router)
app.include_router(maintenance.router)
