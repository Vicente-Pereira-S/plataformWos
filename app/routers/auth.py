from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
import re

from app import models, schemas
from app.database import get_db
from app.utils_auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_optional,
    decode_token_from_cookie,
    mask_email,
)
from app.dependencies import get_templates

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# ------------------------------
# GET: Show registration form
# ------------------------------
@router.get("/register", response_class=HTMLResponse)
def show_register_form(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("register.html", {"request": request})


# ------------------------------
# GET: Show login form
# ------------------------------
@router.get("/login", response_class=HTMLResponse)
def show_login_form(request: Request):
    templates = get_templates(request)
    session_expired = request.session.pop("session_expired", False)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "session_expired": session_expired
    })


# ------------------------------
# API JSON: Register user
# ------------------------------
@router.post("/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pw = hash_password(user_data.password)
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pw,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ------------------------------
# API JSON: Login user
# ------------------------------
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
    ):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    access_token = create_access_token(
        {"sub": str(user.id)}
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ------------------------------
# HTML Form: Logout
# ------------------------------
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response


# ------------------------------
# HTML Form: Register user
# ------------------------------

@router.post("/register-form")
def register_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(None),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    templates = get_templates(request)

    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Passwords do not match",
            "username": username,
            "email": email
        })

    # Validación estricta del nombre de usuario
    if not re.match(r"^[\w\-]{1,15}$", username):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Invalid username format",
            "username": username,
            "email": email
        })

    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username already registered",
            "username": username,
            "email": email
        })

    hashed_pw = hash_password(password)
    new_user = models.User(
        username=username,
        email=email,
        hashed_password=hashed_pw,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return templates.TemplateResponse("registro_exitoso.html", {"request": request})



# ------------------------------
# HTML Form: Login user
# ------------------------------
@router.post("/login-form")
def login_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    templates = get_templates(request)

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid credentials",
            "username": username
        })

    if not user.is_active:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Account is disabled",
            "username": username
        })

    token_data = {"sub": str(user.id)}
    access_token = create_access_token(data=token_data)

    response = RedirectResponse(url=f"/dashboard?username={user.username}", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


# ------------------------------
# Password Recovery Views
# ------------------------------
@router.get("/recover", response_class=HTMLResponse)
def show_recovery_form(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("recuperar_clave.html", {"request": request})


@router.post("/recover", response_class=HTMLResponse)
def process_recovery_form(
    request: Request,
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    templates = get_templates(request)
    user = db.query(models.User).filter(models.User.username == username).first()

    if user and user.email:
        masked = mask_email(user.email)
        return templates.TemplateResponse("confirmar_envio.html", {
            "request": request,
            "username": username,
            "masked_email": masked
        })
    else:
        return templates.TemplateResponse("sin_correo.html", {
            "request": request,
            "username": username
        })


@router.post("/verify-recovery")
def verify_recovery(request: Request, username: str = Form(...), db: Session = Depends(get_db)):
    templates = get_templates(request)

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return templates.TemplateResponse("usuario_no_existe.html", {
            "request": request,
            "username": username
        })

    if not user.email:
        return templates.TemplateResponse("sin_correo.html", {
            "request": request
        })

    email = user.email
    parts = email.split("@")
    masked_email = parts[0][:5] + "******@" + parts[1][:2] + "****"

    return templates.TemplateResponse("confirmar_envio.html", {
        "request": request,
        "email_mascara": masked_email,
        "username": username
    })


@router.post("/send-recovery")
def send_recovery(request: Request, username: str = Form(...)):
    templates = get_templates(request)
    return templates.TemplateResponse("correo_enviado.html", {
        "request": request,
        "username": username
    })


# ------------------------------
# Get current user (protected)
# ------------------------------
@router.get("/me")
def read_users_me(request: Request):
    user_id = decode_token_from_cookie(request)
    return {"user_id": user_id}
