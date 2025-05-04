#!/bin/bash

echo "Extrayendo textos traducibles..."
pybabel extract -F babel.cfg -o app/translations/messages.pot .

echo "Actualizando archivos .po con nuevas cadenas..."
pybabel update -i app/translations/messages.pot -d app/translations

echo "Compilando archivos .po a .mo..."
pybabel compile -d app/translations

echo "Traducciones listas para revisar, una vez traducidad recuerda ejecutar nuevamente: 'pybabel compile -d app/translations'"


pybabel extract -F babel.cfg -o app/translations/messages.pot .
eliminar fuzzy del .pot
dejar vacio los .po
pybabel update -i app/translations/messages.pot -d app/translations
eliminar fuzzy de ambos .po
pybabel compile -d app/translations
traducir manualmente
pybabel compile -d app/translations
