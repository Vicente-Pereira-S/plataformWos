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
    password: str = Form(...),
    confirm_password: str = Form(...),
    secret_question: str = Form(None),
    secret_answer: str = Form(None),
    db: Session = Depends(get_db)
):
    templates = get_templates(request)

    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Passwords do not match",
            "username": username
        })

    # Validación del username
    if not re.match(r"^[\w\-]{1,15}$", username):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Invalid username format",
            "username": username
        })

    # Usuario duplicado
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username already registered",
            "username": username
        })

    # Crear usuario
    hashed_pw = hash_password(password)
    new_user = models.User(
        username=username,
        hashed_password=hashed_pw,
        is_active=True
    )

    # Solo guarda la pregunta y respuesta si ambas están presentes
    if secret_question and secret_answer:
        new_user.secret_question = secret_question.strip()
        new_user.secret_answer = secret_answer.strip()

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


# ------------------------------
# POST: Verificar si el usuario tiene pregunta secreta
# ------------------------------
@router.post("/recover-question", response_class=HTMLResponse)
def recover_question(
    request: Request,
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    templates = get_templates(request)
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        return templates.TemplateResponse("usuario_no_existe.html", {
            "request": request,
            "username": username
        })

    if not user.secret_question:
        return templates.TemplateResponse("sin_pregunta.html", {
            "request": request,
            "username": username
        })

    return templates.TemplateResponse("mostrar_pregunta.html", {
        "request": request,
        "username": username,
        "question": user.secret_question
    })


# ------------------------------
# POST: Validar respuesta secreta y mostrar formulario de nueva contraseña
# ------------------------------
@router.post("/verify-answer", response_class=HTMLResponse)
def verify_secret_answer(
    request: Request,
    username: str = Form(...),
    secret_answer: str = Form(...),
    db: Session = Depends(get_db)
):
    templates = get_templates(request)
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user or not user.secret_answer:
        return templates.TemplateResponse("usuario_no_existe.html", {
            "request": request
        })

    if user.secret_answer.strip().lower() != secret_answer.strip().lower():
        return templates.TemplateResponse("mostrar_pregunta.html", {
            "request": request,
            "username": username,
            "question": user.secret_question,
            "error": "Respuesta incorrecta"
        })

    return templates.TemplateResponse("nueva_clave.html", {
        "request": request,
        "username": username
    })


# ------------------------------
# POST: Guardar nueva contraseña
# ------------------------------
@router.post("/reset-password", response_class=HTMLResponse)
def reset_password(
    request: Request,
    username: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    templates = get_templates(request)

    if new_password != confirm_password:
        return templates.TemplateResponse("nueva_clave.html", {
            "request": request,
            "username": username,
            "error": "Las contraseñas no coinciden"
        })

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return templates.TemplateResponse("usuario_no_existe.html", {
            "request": request
        })

    user.hashed_password = hash_password(new_password)
    db.commit()

    return templates.TemplateResponse("clave_actualizada.html", {
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
