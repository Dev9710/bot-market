"""
JSON Alert Writer - Écrit les alertes dans un fichier JSON pour l'API dashboard

Utilisé par le scanner V3 pour exposer les alertes via API REST sans DB
"""

import json
import os
from threading import Lock
from datetime import datetime

class JSONAlertWriter:
    def __init__(self, file_path='alerts_live.json'):
        self.file_path = file_path
        self.lock = Lock()
        self.max_alerts = 1000  # Garder max 1000 alertes en mémoire

        # Créer le fichier s'il n'existe pas
        if not os.path.exists(self.file_path):
            self._write_alerts([])

    def _load_alerts(self):
        """Charge les alertes depuis le fichier."""
        try:
            with self.lock:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur lecture {self.file_path}: {e}")
            return []

    def _write_alerts(self, alerts):
        """Écrit les alertes dans le fichier."""
        try:
            with self.lock:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(alerts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur écriture {self.file_path}: {e}")

    def add_alert(self, alert_data):
        """
        Ajoute une nouvelle alerte au fichier JSON.

        alert_data doit être un dict avec au minimum:
        - pool_address
        - network
        - token_name
        - token_symbol
        - score
        - tier
        - price
        - liquidity
        - volume_24h
        - age_hours
        """
        # Ajouter timestamp si absent
        if 'created_at' not in alert_data:
            alert_data['created_at'] = datetime.now().isoformat()

        # Charger alertes existantes
        alerts = self._load_alerts()

        # Ajouter la nouvelle
        alerts.append(alert_data)

        # Garder seulement les N dernières
        if len(alerts) > self.max_alerts:
            alerts = alerts[-self.max_alerts:]

        # Sauvegarder
        self._write_alerts(alerts)

        return True

    def get_stats(self):
        """Retourne des stats sur le fichier JSON."""
        alerts = self._load_alerts()
        return {
            'total': len(alerts),
            'file_path': self.file_path,
            'max_capacity': self.max_alerts
        }
