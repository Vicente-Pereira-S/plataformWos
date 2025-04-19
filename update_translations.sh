#!/bin/bash

echo "Extrayendo textos traducibles..."
pybabel extract -F babel.cfg -o app/translations/messages.pot .

echo "Actualizando archivos .po con nuevas cadenas..."
pybabel update -i app/translations/messages.pot -d app/translations

echo "Compilando archivos .po a .mo..."
pybabel compile -d app/translations

echo "Traducciones listas para revisar, una vez traducidad recuerda ejecutar nuevamente: 'compile -d app/translations'"
