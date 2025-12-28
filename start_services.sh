#!/bin/bash

# Démarrer le scanner V3 en arrière-plan
echo "🔍 Démarrage du Scanner V3 en arrière-plan..."
python geckoterminal_scanner_v3.py &

# Attendre 3 secondes pour que le scanner démarre
sleep 3

# Démarrer Gunicorn en premier plan (bloque le script)
echo "📊 Démarrage de l'API Dashboard avec Gunicorn..."
exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 --access-logfile - wsgi:app
