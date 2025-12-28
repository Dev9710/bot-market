#!/bin/bash

# Script de démarrage combiné pour Railway
# Lance le scanner V3 ET l'API dashboard en parallèle

echo "🚀 Démarrage du scanner V3 + Dashboard API"

# Lancer l'API Dashboard en arrière-plan
echo "📊 Démarrage de l'API Dashboard sur port 5000..."
python railway_db_api.py &
API_PID=$!

# Attendre que l'API démarre
sleep 3

# Lancer le scanner V3
echo "🔍 Démarrage du Scanner V3..."
python geckoterminal_scanner_v3.py &
SCANNER_PID=$!

# Fonction pour arrêter proprement les deux processus
cleanup() {
    echo "🛑 Arrêt des services..."
    kill $API_PID 2>/dev/null
    kill $SCANNER_PID 2>/dev/null
    exit 0
}

# Capturer SIGTERM pour arrêt propre
trap cleanup SIGTERM SIGINT

# Attendre que l'un des processus se termine
wait -n

# Si l'un se termine, arrêter l'autre
cleanup
