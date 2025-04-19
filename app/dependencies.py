import os
import gettext
from fastapi.templating import Jinja2Templates
from fastapi import Request

AVAILABLE_LANGS = {"es", "en", "ko", "tr"}

def get_templates(request: Request) -> Jinja2Templates:
    lang = request.cookies.get("preferred_lang", "es")
    if lang not in AVAILABLE_LANGS:
        lang = "es"

    mo_path = os.path.join("app", "translations", lang, "LC_MESSAGES", "messages.mo")

    if os.path.exists(mo_path):
        with open(mo_path, "rb") as f:
            lang_translations = gettext.GNUTranslations(f)
    else:
        lang_translations = gettext.NullTranslations()

    templates = Jinja2Templates(directory="app/templates")
    templates.env.globals.update({
        '_': lang_translations.gettext,
        'get_locale': lambda: lang
    })
    return templates
