# 🛠️ Plataforma de Citas MMO – Skariio

Esta es una plataforma web desarrollada en **FastAPI** y **Bootstrap**, pensada para organizar citas de buffs en juegos MMO. Los usuarios pueden registrarse, iniciar sesión y ver/organizar citas automáticamente con soporte multilenguaje.

## 🚀 Características principales

- Registro e inicio de sesión con JWT
- Persistencia de idioma mediante cookies (i18n: Español, Inglés, Coreano, Turco)
- Interfaz responsiva con Bootstrap 5
- Roles de usuario: observador, miembro, líder, administrador
- Traducciones usando `gettext`, `.po/.mo` y Babel
- Control de errores amigable y traducido
- Almacenamiento local con SQLite
- Preparado para despliegue en Render

## 📦 Tecnologías utilizadas

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Bootstrap 5](https://getbootstrap.com/)
- [Jinja2](https://jinja.palletsprojects.com/)
- [gettext / Babel](https://babel.pocoo.org/)
- SQLite (solo para desarrollo local)

## 🔧 Instalación local

```bash
git clone https://github.com/Vicente-Pereira-S/plataformaWos.git
cd plataformaWos
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz:

```
SESSION_SECRET_KEY se utiliza para las sesiones seguras de la app (cookies).
SECRET_KEY se usa internamente para generar tokens JWT u otras operaciones sensibles.

```

## 🧪 Ejecutar en desarrollo

```bash
uvicorn app.main:app --reload
```

Abre tu navegador en [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 🌍 Traducciones

Para actualizar traducciones, usa el script incluido:

```bash
./update_translations.sh
```

## 📁 Estructura del proyecto

```
.
├── app/
│   ├── templates/
│   ├── static/
│   ├── routers/
│   ├── translations/
│   ├── models.py
│   ├── schemas.py
│   ├── utils_auth.py
│   └── ...
├── .env
├── .gitignore
├── requirements.txt
├── update_translations.sh
├── README.md
└── database.db
```

## 📌 Notas

- El email es opcional al registrarse (solo para recuperar contraseña)
- El sistema es funcional y minimalista: ¡simple pero poderoso!
- Este proyecto forma parte de mi portafolio personal como backend developer

## 🧑‍💻 Autor

Desarrollado por **Vicente Pereira**

---

*¿Te gustó el proyecto? ¡Dale una ⭐ en GitHub!*