#!/bin/bash

# Créer la table alerts dans PostgreSQL si elle n'existe pas
echo "🔧 Création de la table alerts dans PostgreSQL..."
python create_alerts_table_postgres.py
echo ""

# Migration SQLite - Ajouter les colonnes de tracking prix
echo "🔧 Migration SQLite - Ajout colonnes de tracking..."
python migrate_sqlite_db.py
echo ""

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

# Cron job - Price Tracker (toutes les heures)
price_tracker_cron() {
    echo "[PRICE TRACKER] Process demarré - PID: $$"

    # Premier run après 5 minutes (pour laisser le scanner démarrer)
    echo "[PRICE TRACKER] Premier run dans 5 minutes..."
    sleep 300

    while true; do
        echo "[PRICE TRACKER] ======================================"
        echo "[PRICE TRACKER] Démarrage du tracking - $(date)"
        echo "[PRICE TRACKER] ======================================"

        python price_tracker_cron_railway.py
        EXIT_CODE=$?

        if [ $EXIT_CODE -eq 0 ]; then
            echo "[PRICE TRACKER] Tracking terminé avec succès"
        else
            echo "[PRICE TRACKER] ERREUR lors du tracking (code: $EXIT_CODE)"
        fi

        echo "[PRICE TRACKER] Prochain run dans 1 heure..."
        sleep 3600
    done
}

# Démarrer le scanner avec surveillance en arrière-plan
echo "🔍 Démarrage du Scanner V3 avec surveillance auto-restart..."
monitor_scanner &
SCANNER_PID=$!
echo "Scanner PID: $SCANNER_PID"

# Démarrer le price tracker cron job en arrière-plan
echo "⏰ Démarrage du Price Tracker (cron toutes les heures)..."
price_tracker_cron &
TRACKER_PID=$!
echo "Price Tracker PID: $TRACKER_PID"

# Attendre 5 secondes pour que les processus démarrent
sleep 5

# Vérifier que les processus sont bien lancés
echo "Vérification des processus..."
if kill -0 $SCANNER_PID 2>/dev/null; then
    echo "✅ Scanner actif (PID: $SCANNER_PID)"
else
    echo "❌ Scanner non démarré!"
fi

if kill -0 $TRACKER_PID 2>/dev/null; then
    echo "✅ Price Tracker actif (PID: $TRACKER_PID)"
else
    echo "❌ Price Tracker non démarré!"
fi

# Démarrer Gunicorn en premier plan (bloque le script)
# NOTE: Les processus background continuent de tourner car ils sont des enfants du shell
echo "📊 Démarrage de l'API Dashboard avec Gunicorn..."
gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 --access-logfile - --error-logfile - --log-level debug wsgi:app
