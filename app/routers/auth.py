from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse

from app import models, schemas, utils_auth as auth
from app.database import get_db
from app.utils_auth import get_current_user
from app.dependencies import get_templates

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# ----------------------------
# REGISTRO Y LOGIN API (JSON)
# ----------------------------

@router.post("/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Nombre de usuario ya registrado")

    hashed_pw = auth.hash_password(user_data.password)
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pw,
        role="observador",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    token_data = {"sub": str(user.id)}
    access_token = auth.create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response


# ----------------------------
# FORMULARIOS HTML
# ----------------------------

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
            "error": "Las contraseñas no coinciden"
        })

    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Nombre de usuario ya registrado"
        })

    hashed_pw = auth.hash_password(password)
    new_user = models.User(
        username=username,
        email=email,
        hashed_password=hashed_pw,
        role="observador",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return templates.TemplateResponse("registro_exitoso.html", {"request": request})


@router.post("/login-form")
def login_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    templates = get_templates(request)

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Credenciales inválidas",
            "username": username
        })

    if not user.is_active:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Tu cuenta está desactivada",
            "username": username
        })

    token_data = {"sub": str(user.id)}
    access_token = auth.create_access_token(data=token_data)

    response = RedirectResponse(url=f"/dashboard?username={user.username}", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


# ----------------------------
# RECUPERACIÓN DE CONTRASEÑA
# ----------------------------

@router.get("/recuperar-clave")
def recuperar_clave(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("recuperar_clave.html", {"request": request})


@router.post("/verificar-recuperacion")
def verificar_recuperacion(request: Request, username: str = Form(...), db: Session = Depends(get_db)):
    templates = get_templates(request)

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        # Usuario no existe
        return templates.TemplateResponse("usuario_no_existe.html", {
            "request": request,
            "username": username
        })

    if not user.email:
        # Usuario sin correo registrado
        return templates.TemplateResponse("sin_correo.html", {
            "request": request
        })

    # Usuario con correo válido → enmascarar
    email = user.email
    partes = email.split("@")
    email_mascara = partes[0][:5] + "******@" + partes[1][:2] + "****"

    return templates.TemplateResponse("confirmar_envio.html", {
        "request": request,
        "email_mascara": email_mascara,
        "username": username
    })




@router.post("/enviar-recuperacion")
def enviar_recuperacion(request: Request, username: str = Form(...)):
    templates = get_templates(request)
    return templates.TemplateResponse("correo_enviado.html", {
        "request": request,
        "username": username
    })


# ----------------------------
# RUTA DE PERFIL PROTEGIDA
# ----------------------------

@router.get("/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }


# ----------------------------
# FORMULARIOS VISUALES (GET)
# ----------------------------

@router.get("/login")
def show_login_form(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register")
def show_register_form(request: Request):
    templates = get_templates(request)
    return templates.TemplateResponse("register.html", {"request": request})
