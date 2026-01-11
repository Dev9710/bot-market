#!/bin/bash

# Créer la table alerts dans PostgreSQL si elle n'existe pas
echo "🔧 Création de la table alerts dans PostgreSQL..."
python create_alerts_table_postgres.py
echo ""

# Exécuter la migration de la base de données (déjà fait si table créée ci-dessus)
# echo "🔧 Vérification et migration de la base de données..."
# python migrate_railway_db.py
# echo ""

# Script de surveillance qui redémarre le scanner s'il crash
monitor_scanner() {
    while true; do
        echo "[MONITOR] Démarrage du Scanner V3..."
        python geckoterminal_scanner_v3_main.py

        EXIT_CODE=$?
        echo "[MONITOR] Scanner arrêté avec code: $EXIT_CODE"
        echo "[MONITOR] Redémarrage dans 10 secondes..."
        sleep 10
    done
}

# Démarrer le scanner avec surveillance en arrière-plan
echo "🔍 Démarrage du Scanner V3 avec surveillance auto-restart..."
monitor_scanner &

# Attendre 5 secondes pour que le scanner démarre
sleep 5

# Démarrer Gunicorn en premier plan (bloque le script)
echo "📊 Démarrage de l'API Dashboard avec Gunicorn..."
exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 --access-logfile - --error-logfile - --log-level debug wsgi:app
