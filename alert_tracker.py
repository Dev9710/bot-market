"""
Alert Tracker avec SQLite - Système de mémoire et analyse d'alertes
Sauvegarde toutes les alertes avec prix d'entrée, SL, TP et tracking automatique
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import time
import threading

class AlertTracker:
    def __init__(self, db_path='alerts_history.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
        print(f"✅ AlertTracker initialisé - DB: {db_path}")

    def create_tables(self):
        """Crée les tables de la base de données."""
        cursor = self.conn.cursor()

        # Table principale des alertes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                token_name TEXT NOT NULL,
                token_address TEXT NOT NULL,
                network TEXT NOT NULL,

                -- Prix et scores
                price_at_alert REAL NOT NULL,
                score INTEGER NOT NULL,
                base_score INTEGER,
                momentum_bonus INTEGER,
                confidence_score INTEGER,

                -- Métriques on-chain
                volume_24h REAL,
                volume_6h REAL,
                volume_1h REAL,
                liquidity REAL,
                buys_24h INTEGER,
                sells_24h INTEGER,
                buy_ratio REAL,
                total_txns INTEGER,
                age_hours REAL,

                -- Prix suggérés par l'algo
                entry_price REAL NOT NULL,
                stop_loss_price REAL NOT NULL,
                stop_loss_percent REAL NOT NULL,
                tp1_price REAL NOT NULL,
                tp1_percent REAL NOT NULL,
                tp2_price REAL NOT NULL,
                tp2_percent REAL NOT NULL,
                tp3_price REAL NOT NULL,
                tp3_percent REAL NOT NULL,

                -- Message d'alerte complet
                alert_message TEXT,

                -- Métadonnées
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(token_address, timestamp)
            )
        """)

        # Table de tracking des prix
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                minutes_after_alert INTEGER NOT NULL,
                price REAL NOT NULL,
                roi_percent REAL NOT NULL,

                -- Analyse des niveaux
                sl_hit BOOLEAN DEFAULT 0,
                tp1_hit BOOLEAN DEFAULT 0,
                tp2_hit BOOLEAN DEFAULT 0,
                tp3_hit BOOLEAN DEFAULT 0,
                highest_price REAL,
                lowest_price REAL,

                FOREIGN KEY (alert_id) REFERENCES alerts (id),
                UNIQUE(alert_id, minutes_after_alert)
            )
        """)

        # Table d'analyse de cohérence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,

                -- Résultats
                was_profitable BOOLEAN,
                best_roi_4h REAL,
                worst_roi_4h REAL,
                roi_at_4h REAL,
                roi_at_24h REAL,

                -- Niveaux atteints
                sl_was_hit BOOLEAN DEFAULT 0,
                tp1_was_hit BOOLEAN DEFAULT 0,
                tp2_was_hit BOOLEAN DEFAULT 0,
                tp3_was_hit BOOLEAN DEFAULT 0,

                -- Temps pour atteindre les niveaux (en minutes)
                time_to_sl INTEGER,
                time_to_tp1 INTEGER,
                time_to_tp2 INTEGER,
                time_to_tp3 INTEGER,

                -- Cohérence de l'analyse
                prediction_quality TEXT,
                was_coherent BOOLEAN,
                coherence_notes TEXT,

                -- Métadonnées
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (alert_id) REFERENCES alerts (id),
                UNIQUE(alert_id)
            )
        """)

        # Index pour performances
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_token ON alerts(token_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tracking_alert ON price_tracking(alert_id)")

        # Ajouter les nouvelles colonnes pour l'accélération du volume (si elles n'existent pas)
        try:
            cursor.execute("ALTER TABLE alerts ADD COLUMN volume_acceleration_1h_vs_6h REAL DEFAULT 0")
            print("✅ Colonne volume_acceleration_1h_vs_6h ajoutée")
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà

        try:
            cursor.execute("ALTER TABLE alerts ADD COLUMN volume_acceleration_6h_vs_24h REAL DEFAULT 0")
            print("✅ Colonne volume_acceleration_6h_vs_24h ajoutée")
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà

        # Ajouter colonnes pour RÈGLE 5 - Vélocité du pump
        try:
            cursor.execute("ALTER TABLE alerts ADD COLUMN velocite_pump REAL DEFAULT 0")
            print("✅ Colonne velocite_pump ajoutée")
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà

        try:
            cursor.execute("ALTER TABLE alerts ADD COLUMN type_pump TEXT DEFAULT 'UNKNOWN'")
            print("✅ Colonne type_pump ajoutée")
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà

        try:
            cursor.execute("ALTER TABLE alerts ADD COLUMN decision_tp_tracking TEXT DEFAULT NULL")
            print("✅ Colonne decision_tp_tracking ajoutée")
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà

        try:
            cursor.execute("ALTER TABLE alerts ADD COLUMN temps_depuis_alerte_precedente REAL DEFAULT 0")
            print("✅ Colonne temps_depuis_alerte_precedente ajoutée")
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà

        try:
            cursor.execute("ALTER TABLE alerts ADD COLUMN is_alerte_suivante INTEGER DEFAULT 0")
            print("✅ Colonne is_alerte_suivante ajoutée")
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà

        self.conn.commit()
        print("✅ Tables créées avec succès")

    def save_alert(self, alert_data: Dict) -> int:
        """
        Sauvegarde une nouvelle alerte.

        Args:
            alert_data: Dict contenant toutes les données de l'alerte

        Returns:
            alert_id: ID de l'alerte créée
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO alerts (
                    token_name, token_address, network,
                    price_at_alert, score, base_score, momentum_bonus, confidence_score,
                    volume_24h, volume_6h, volume_1h, liquidity,
                    buys_24h, sells_24h, buy_ratio, total_txns, age_hours,
                    entry_price, stop_loss_price, stop_loss_percent,
                    tp1_price, tp1_percent, tp2_price, tp2_percent,
                    tp3_price, tp3_percent, alert_message,
                    volume_acceleration_1h_vs_6h, volume_acceleration_6h_vs_24h,
                    velocite_pump, type_pump, decision_tp_tracking,
                    temps_depuis_alerte_precedente, is_alerte_suivante
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_data['token_name'],
                alert_data['token_address'],
                alert_data['network'],
                alert_data['price_at_alert'],
                alert_data['score'],
                alert_data.get('base_score'),
                alert_data.get('momentum_bonus'),
                alert_data.get('confidence_score'),
                alert_data.get('volume_24h'),
                alert_data.get('volume_6h'),
                alert_data.get('volume_1h'),
                alert_data.get('liquidity'),
                alert_data.get('buys_24h'),
                alert_data.get('sells_24h'),
                alert_data.get('buy_ratio'),
                alert_data.get('total_txns'),
                alert_data.get('age_hours'),
                alert_data['entry_price'],
                alert_data['stop_loss_price'],
                alert_data['stop_loss_percent'],
                alert_data['tp1_price'],
                alert_data['tp1_percent'],
                alert_data['tp2_price'],
                alert_data['tp2_percent'],
                alert_data['tp3_price'],
                alert_data['tp3_percent'],
                alert_data.get('alert_message', ''),
                alert_data.get('volume_acceleration_1h_vs_6h', 0),
                alert_data.get('volume_acceleration_6h_vs_24h', 0),
                alert_data.get('velocite_pump', 0),
                alert_data.get('type_pump', 'UNKNOWN'),
                alert_data.get('decision_tp_tracking', None),
                alert_data.get('temps_depuis_alerte_precedente', 0),
                alert_data.get('is_alerte_suivante', 0)
            ))

            self.conn.commit()
            alert_id = cursor.lastrowid

            print(f"✅ Alerte sauvegardée - ID: {alert_id} - Token: {alert_data['token_name']}")

            # Démarrer le tracking automatique en arrière-plan
            self.start_price_tracking(alert_id, alert_data['token_address'], alert_data['network'])

            return alert_id

        except sqlite3.IntegrityError as e:
            print(f"⚠️ Alerte déjà existante pour {alert_data['token_name']} à ce timestamp")
            return -1
        except Exception as e:
            print(f"❌ Erreur sauvegarde alerte: {e}")
            self.conn.rollback()
            return -1

    def start_price_tracking(self, alert_id: int, token_address: str, network: str):
        """
        Démarre le tracking automatique des prix à intervalles définis.

        Args:
            alert_id: ID de l'alerte
            token_address: Adresse du token
            network: Réseau (eth, bsc, etc.)
        """
        # Intervalles de tracking (en minutes)
        intervals = [15, 60, 240, 1440]  # 15min, 1h, 4h, 24h

        def track_at_interval(minutes):
            """Fonction qui sera appelée après X minutes."""
            time.sleep(minutes * 60)
            self.update_price_tracking(alert_id, token_address, network, minutes)

            # Si c'est le tracking 24h, faire l'analyse finale
            if minutes == 1440:
                self.analyze_alert_performance(alert_id)

        # Lancer un thread pour chaque intervalle
        for interval in intervals:
            thread = threading.Thread(
                target=track_at_interval,
                args=(interval,),
                daemon=True,
                name=f"Tracker-{alert_id}-{interval}min"
            )
            thread.start()

        print(f"📊 Tracking démarré pour alerte {alert_id} aux intervalles: {intervals} minutes")

    def update_price_tracking(self, alert_id: int, token_address: str, network: str, minutes_after: int):
        """
        Met à jour le tracking du prix à un moment donné.

        Args:
            alert_id: ID de l'alerte
            token_address: Adresse du token
            network: Réseau
            minutes_after: Minutes écoulées depuis l'alerte
        """
        try:
            # Récupérer les données de l'alerte
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT price_at_alert, entry_price, stop_loss_price,
                       tp1_price, tp2_price, tp3_price
                FROM alerts WHERE id = ?
            """, (alert_id,))

            result = cursor.fetchone()
            if not result:
                print(f"⚠️ Alerte {alert_id} introuvable")
                return

            price_at_alert, entry_price, sl_price, tp1_price, tp2_price, tp3_price = result

            # Récupérer le prix actuel (fonction à implémenter selon ton API)
            current_price = self.fetch_current_price(token_address, network)

            if current_price is None or current_price <= 0:
                print(f"⚠️ Prix invalide pour {token_address} - Skip tracking")
                return

            # Calculer le ROI
            roi = ((current_price - entry_price) / entry_price) * 100

            # Vérifier quels niveaux ont été touchés
            sl_hit = current_price <= sl_price
            tp1_hit = current_price >= tp1_price
            tp2_hit = current_price >= tp2_price
            tp3_hit = current_price >= tp3_price

            # Récupérer le plus haut/plus bas depuis l'alerte
            cursor.execute("""
                SELECT MAX(price), MIN(price) FROM price_tracking
                WHERE alert_id = ?
            """, (alert_id,))
            highest, lowest = cursor.fetchone()

            highest_price = max(current_price, highest or current_price)
            lowest_price = min(current_price, lowest or current_price)

            # Insérer ou mettre à jour le tracking
            cursor.execute("""
                INSERT OR REPLACE INTO price_tracking (
                    alert_id, minutes_after_alert, price, roi_percent,
                    sl_hit, tp1_hit, tp2_hit, tp3_hit,
                    highest_price, lowest_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_id, minutes_after, current_price, roi,
                sl_hit, tp1_hit, tp2_hit, tp3_hit,
                highest_price, lowest_price
            ))

            self.conn.commit()

            # Log
            status = []
            if sl_hit:
                status.append("🔴 SL HIT")
            if tp3_hit:
                status.append("🟢🟢🟢 TP3 HIT")
            elif tp2_hit:
                status.append("🟢🟢 TP2 HIT")
            elif tp1_hit:
                status.append("🟢 TP1 HIT")

            status_str = " | ".join(status) if status else "📊 En cours"

            print(f"📊 Tracking {minutes_after}min - Alerte {alert_id} - ROI: {roi:+.2f}% - {status_str}")

        except Exception as e:
            print(f"❌ Erreur tracking alerte {alert_id}: {e}")

    def fetch_current_price(self, token_address: str, network: str) -> Optional[float]:
        """
        Récupère le prix actuel d'un token via DexScreener API.

        Args:
            token_address: Adresse du token
            network: Réseau (eth, bsc, etc.)

        Returns:
            Prix actuel ou None si erreur
        """
        try:
            import requests

            # Méthode 1: DexScreener API (fonctionne pour tous les réseaux)
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])

                if not pairs:
                    print(f"⚠️ Aucune paire trouvée pour {token_address[:10]}...")
                    return None

                # Prendre la paire avec le plus de liquidité
                main_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))
                price = float(main_pair.get('priceUsd', 0))

                if price > 0:
                    return price
                else:
                    print(f"⚠️ Prix invalide (0) pour {token_address[:10]}...")
                    return None

            # Méthode 2 (fallback): GeckoTerminal API
            network_map = {
                'eth': 'ethereum',
                'bsc': 'bsc',
                'polygon': 'polygon',
                'arbitrum': 'arbitrum',
                'base': 'base',
                'avalanche': 'avalanche',
                'optimism': 'optimism'
            }

            gecko_network = network_map.get(network, network)
            url = f"https://api.geckoterminal.com/api/v2/networks/{gecko_network}/tokens/{token_address}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                price_usd = float(data.get('data', {}).get('attributes', {}).get('price_usd', 0))

                if price_usd > 0:
                    return price_usd

            print(f"⚠️ Impossible de récupérer le prix pour {token_address[:10]}... sur {network}")
            return None

        except Exception as e:
            print(f"❌ Erreur fetch price {token_address[:10]}...: {e}")
            return None

    def analyze_alert_performance(self, alert_id: int):
        """
        Analyse la performance globale d'une alerte après 24h.

        Args:
            alert_id: ID de l'alerte
        """
        try:
            cursor = self.conn.cursor()

            # Récupérer tous les trackings
            cursor.execute("""
                SELECT minutes_after_alert, price, roi_percent,
                       sl_hit, tp1_hit, tp2_hit, tp3_hit
                FROM price_tracking
                WHERE alert_id = ?
                ORDER BY minutes_after_alert
            """, (alert_id,))

            trackings = cursor.fetchall()

            if not trackings:
                print(f"⚠️ Aucun tracking pour alerte {alert_id}")
                return

            # Extraire les données
            prices = [t[1] for t in trackings]
            rois = [t[2] for t in trackings]

            best_roi = max(rois)
            worst_roi = min(rois)

            # ROI aux points clés
            roi_4h = next((t[2] for t in trackings if t[0] == 240), None)
            roi_24h = next((t[2] for t in trackings if t[0] == 1440), None)

            # Niveaux atteints
            sl_hit = any(t[3] for t in trackings)
            tp1_hit = any(t[4] for t in trackings)
            tp2_hit = any(t[5] for t in trackings)
            tp3_hit = any(t[6] for t in trackings)

            # Temps pour atteindre chaque niveau
            time_to_sl = next((t[0] for t in trackings if t[3]), None)
            time_to_tp1 = next((t[0] for t in trackings if t[4]), None)
            time_to_tp2 = next((t[0] for t in trackings if t[5]), None)
            time_to_tp3 = next((t[0] for t in trackings if t[6]), None)

            # Évaluation de la qualité de prédiction
            was_profitable = roi_4h and roi_4h > 5

            # Récupérer le score original
            cursor.execute("SELECT score FROM alerts WHERE id = ?", (alert_id,))
            score = cursor.fetchone()[0]

            # Cohérence : score élevé devrait donner profit
            was_coherent = (score >= 70 and was_profitable) or (score < 70 and not was_profitable)

            # Notes de cohérence
            if tp3_hit:
                prediction_quality = "EXCELLENT"
                coherence_notes = "TP3 atteint - Prédiction parfaite"
            elif tp2_hit:
                prediction_quality = "TRÈS BON"
                coherence_notes = "TP2 atteint - Bonne prédiction"
            elif tp1_hit:
                prediction_quality = "BON"
                coherence_notes = "TP1 atteint - Prédiction correcte"
            elif sl_hit:
                prediction_quality = "MAUVAIS"
                coherence_notes = "Stop Loss touché - Prédiction incorrecte"
            else:
                prediction_quality = "MOYEN"
                coherence_notes = "Aucun niveau significatif atteint"

            # Sauvegarder l'analyse
            cursor.execute("""
                INSERT OR REPLACE INTO alert_analysis (
                    alert_id, was_profitable, best_roi_4h, worst_roi_4h,
                    roi_at_4h, roi_at_24h,
                    sl_was_hit, tp1_was_hit, tp2_was_hit, tp3_was_hit,
                    time_to_sl, time_to_tp1, time_to_tp2, time_to_tp3,
                    prediction_quality, was_coherent, coherence_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_id, was_profitable, best_roi, worst_roi,
                roi_4h, roi_24h,
                sl_hit, tp1_hit, tp2_hit, tp3_hit,
                time_to_sl, time_to_tp1, time_to_tp2, time_to_tp3,
                prediction_quality, was_coherent, coherence_notes
            ))

            self.conn.commit()

            print(f"\n{'='*80}")
            print(f"📊 ANALYSE FINALE - Alerte {alert_id}")
            print(f"{'='*80}")
            print(f"ROI 4h: {roi_4h:+.2f}% | ROI 24h: {roi_24h:+.2f}%")
            print(f"Meilleur ROI: {best_roi:+.2f}% | Pire ROI: {worst_roi:+.2f}%")
            print(f"Niveaux atteints: SL={sl_hit} | TP1={tp1_hit} | TP2={tp2_hit} | TP3={tp3_hit}")
            print(f"Qualité: {prediction_quality} | Cohérent: {was_coherent}")
            print(f"Notes: {coherence_notes}")
            print(f"{'='*80}\n")

        except Exception as e:
            print(f"❌ Erreur analyse alerte {alert_id}: {e}")

    def token_already_alerted(self, token_address: str) -> bool:
        """
        Vérifie si un token a déjà reçu une alerte.

        Args:
            token_address: Adresse du token

        Returns:
            True si le token a déjà été alerté, False sinon
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM alerts
            WHERE token_address = ?
        """, (token_address,))

        count = cursor.fetchone()[0]
        return count > 0

    def get_last_alert_for_token(self, token_address: str) -> Optional[Dict]:
        """
        Récupère la dernière alerte pour un token donné.

        Args:
            token_address: Adresse du token

        Returns:
            Dict avec les données de la dernière alerte, ou None si aucune alerte
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                id, token_name, token_address, network,
                price_at_alert, score, base_score, momentum_bonus,
                confidence_score, volume_24h, volume_6h, volume_1h,
                liquidity, buys_24h, sells_24h, buy_ratio,
                total_txns, age_hours, created_at,
                entry_price, stop_loss_price, stop_loss_percent,
                tp1_price, tp1_percent, tp2_price, tp2_percent,
                tp3_price, tp3_percent,
                volume_acceleration_1h_vs_6h, volume_acceleration_6h_vs_24h,
                velocite_pump, type_pump, decision_tp_tracking,
                temps_depuis_alerte_precedente, is_alerte_suivante
            FROM alerts
            WHERE token_address = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (token_address,))

        row = cursor.fetchone()
        if not row:
            return None

        columns = [
            'id', 'token_name', 'token_address', 'network',
            'price_at_alert', 'score', 'base_score', 'momentum_bonus',
            'confidence_score', 'volume_24h', 'volume_6h', 'volume_1h',
            'liquidity', 'buys_24h', 'sells_24h', 'buy_ratio',
            'total_txns', 'age_hours', 'created_at',
            'entry_price', 'stop_loss_price', 'stop_loss_percent',
            'tp1_price', 'tp1_percent', 'tp2_price', 'tp2_percent',
            'tp3_price', 'tp3_percent',
            'volume_acceleration_1h_vs_6h', 'volume_acceleration_6h_vs_24h',
            'velocite_pump', 'type_pump', 'decision_tp_tracking',
            'temps_depuis_alerte_precedente', 'is_alerte_suivante'
        ]

        return dict(zip(columns, row))

    def get_active_alerts(self, max_age_hours: int = 24) -> List[Dict]:
        """
        Récupère toutes les alertes actives (créées dans les dernières X heures).
        Utilisé pour le tracking actif des pools alertés.

        Args:
            max_age_hours: Age maximum en heures (défaut: 24h)

        Returns:
            Liste de Dict contenant les données des alertes actives
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                id, token_name, token_address, network,
                price_at_alert, score, entry_price,
                tp1_price, tp2_price, tp3_price,
                stop_loss_price, created_at
            FROM alerts
            WHERE datetime(created_at) >= datetime('now', ? || ' hours')
            ORDER BY created_at DESC
        """, (f'-{max_age_hours}',))

        rows = cursor.fetchall()

        columns = [
            'id', 'token_name', 'token_address', 'network',
            'price_at_alert', 'score', 'entry_price',
            'tp1_price', 'tp2_price', 'tp3_price',
            'stop_loss_price', 'created_at'
        ]

        return [dict(zip(columns, row)) for row in rows]

    def update_price_max_realtime(self, alert_id: int, current_price: float):
        """
        Met à jour le prix MAX en temps réel à chaque scan (toutes les 2 min).
        CRITIQUE pour backtesting précis : capture TOUS les pics de prix.

        Args:
            alert_id: ID de l'alerte
            current_price: Prix actuel du token

        Returns:
            True si update réussi, False sinon
        """
        try:
            cursor = self.conn.cursor()

            # Récupérer l'entry price pour calculer ROI
            cursor.execute("SELECT entry_price FROM alerts WHERE id = ?", (alert_id,))
            result = cursor.fetchone()
            if not result:
                return False

            entry_price = result[0]

            # Calculer combien de minutes depuis l'alerte
            cursor.execute("""
                SELECT CAST((julianday('now') - julianday(created_at)) * 1440 AS INTEGER) as minutes_elapsed
                FROM alerts WHERE id = ?
            """, (alert_id,))
            minutes_elapsed = cursor.fetchone()[0]

            # Récupérer le prix MAX actuel depuis price_tracking
            cursor.execute("""
                SELECT MAX(highest_price) FROM price_tracking
                WHERE alert_id = ?
            """, (alert_id,))

            current_max = cursor.fetchone()[0]

            # Déterminer le nouveau prix MAX
            if current_max is None:
                new_max = current_price
            else:
                new_max = max(float(current_max), current_price)

            # Calculer ROI
            roi = ((current_price - entry_price) / entry_price) * 100

            # Insérer ou mettre à jour le tracking temps réel
            # Note: On utilise minutes_elapsed = 0 pour les updates temps réel
            # Les updates schedulés (15min, 1h, etc.) utilisent leurs propres minutes
            cursor.execute("""
                INSERT INTO price_tracking (
                    alert_id, minutes_after_alert, price, roi_percent,
                    highest_price, lowest_price, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(alert_id, minutes_after_alert) DO UPDATE SET
                    price = excluded.price,
                    roi_percent = excluded.roi_percent,
                    highest_price = MAX(highest_price, excluded.highest_price),
                    lowest_price = MIN(COALESCE(lowest_price, 999999), excluded.price),
                    timestamp = excluded.timestamp
            """, (
                alert_id,
                minutes_elapsed,  # Minutes exactes depuis création
                current_price,
                roi,
                new_max,
                current_price  # lowest_price initialisé au prix actuel
            ))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"❌ Erreur update prix_max realtime pour alerte {alert_id}: {e}")
            return False

    def get_highest_price_for_alert(self, alert_id: int) -> Optional[float]:
        """
        Récupère le prix MAX atteint depuis une alerte donnée (depuis price_tracking).

        Args:
            alert_id: ID de l'alerte

        Returns:
            Prix maximum atteint, ou None si pas de tracking disponible
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT MAX(highest_price) FROM price_tracking
            WHERE alert_id = ?
        """, (alert_id,))

        result = cursor.fetchone()
        if result and result[0]:
            return float(result[0])
        return None

    def get_token_history(self, token_name: str) -> List[Dict]:
        """
        Récupère l'historique complet d'un token.

        Args:
            token_name: Nom du token

        Returns:
            Liste des alertes avec leurs trackings et analyses
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT a.*,
                   an.was_profitable, an.roi_at_4h, an.roi_at_24h,
                   an.prediction_quality, an.coherence_notes
            FROM alerts a
            LEFT JOIN alert_analysis an ON a.id = an.alert_id
            WHERE a.token_name = ?
            ORDER BY a.timestamp DESC
        """, (token_name,))

        columns = [desc[0] for desc in cursor.description]
        results = []

        for row in cursor.fetchall():
            alert = dict(zip(columns, row))

            # Récupérer les trackings
            cursor.execute("""
                SELECT minutes_after_alert, price, roi_percent,
                       sl_hit, tp1_hit, tp2_hit, tp3_hit
                FROM price_tracking
                WHERE alert_id = ?
                ORDER BY minutes_after_alert
            """, (alert['id'],))

            alert['trackings'] = [
                {
                    'minutes': t[0],
                    'price': t[1],
                    'roi': t[2],
                    'sl_hit': bool(t[3]),
                    'tp1_hit': bool(t[4]),
                    'tp2_hit': bool(t[5]),
                    'tp3_hit': bool(t[6])
                }
                for t in cursor.fetchall()
            ]

            results.append(alert)

        return results

    def get_performance_stats(self) -> Dict:
        """
        Retourne les statistiques globales de performance.

        Returns:
            Dict avec les stats
        """
        cursor = self.conn.cursor()

        # Total alertes
        cursor.execute("SELECT COUNT(*) FROM alerts")
        total_alerts = cursor.fetchone()[0]

        # Alertes analysées (24h passées)
        cursor.execute("SELECT COUNT(*) FROM alert_analysis")
        analyzed_alerts = cursor.fetchone()[0]

        # Taux de cohérence
        cursor.execute("SELECT COUNT(*) FROM alert_analysis WHERE was_coherent = 1")
        coherent_count = cursor.fetchone()[0]
        coherence_rate = (coherent_count / analyzed_alerts * 100) if analyzed_alerts > 0 else 0

        # ROI moyen par tranche de score
        cursor.execute("""
            SELECT
                CAST(a.score / 10 AS INTEGER) * 10 as score_range,
                AVG(an.roi_at_4h) as avg_roi_4h,
                COUNT(*) as count
            FROM alerts a
            JOIN alert_analysis an ON a.id = an.alert_id
            GROUP BY score_range
            ORDER BY score_range
        """)
        roi_by_score = {f"{row[0]}-{row[0]+9}": {'avg_roi': row[1], 'count': row[2]}
                       for row in cursor.fetchall()}

        # Taux de succès par niveau
        cursor.execute("""
            SELECT
                SUM(CASE WHEN tp1_was_hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as tp1_rate,
                SUM(CASE WHEN tp2_was_hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as tp2_rate,
                SUM(CASE WHEN tp3_was_hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as tp3_rate,
                SUM(CASE WHEN sl_was_hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as sl_rate
            FROM alert_analysis
        """)
        tp_rates = cursor.fetchone()

        return {
            'total_alerts': total_alerts,
            'analyzed_alerts': analyzed_alerts,
            'coherence_rate': coherence_rate,
            'roi_by_score': roi_by_score,
            'tp1_hit_rate': tp_rates[0] if tp_rates else 0,
            'tp2_hit_rate': tp_rates[1] if tp_rates else 0,
            'tp3_hit_rate': tp_rates[2] if tp_rates else 0,
            'sl_hit_rate': tp_rates[3] if tp_rates else 0
        }

    def print_stats(self):
        """Affiche les statistiques dans la console."""
        stats = self.get_performance_stats()

        print("\n" + "="*80)
        print("📊 STATISTIQUES DE PERFORMANCE")
        print("="*80)
        print(f"Total alertes envoyées: {stats['total_alerts']}")
        print(f"Alertes analysées (24h+): {stats['analyzed_alerts']}")
        print(f"Taux de cohérence: {stats['coherence_rate']:.1f}%")
        print(f"\nTaux d'atteinte des niveaux:")
        print(f"  TP1: {stats['tp1_hit_rate'] or 0:.1f}%")
        print(f"  TP2: {stats['tp2_hit_rate'] or 0:.1f}%")
        print(f"  TP3: {stats['tp3_hit_rate'] or 0:.1f}%")
        print(f"  Stop Loss: {stats['sl_hit_rate'] or 0:.1f}%")
        print(f"\nROI moyen par tranche de score:")
        for score_range, data in stats['roi_by_score'].items():
            print(f"  Score {score_range}: {data['avg_roi']:+.2f}% ({data['count']} alertes)")
        print("="*80 + "\n")

    def close(self):
        """Ferme la connexion à la base de données."""
        self.conn.close()
        print("✅ Connexion DB fermée")


# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser le tracker
    tracker = AlertTracker()

    # Exemple: sauvegarder une alerte
    alert_data = {
        'token_name': 'PEPE',
        'token_address': '0x6982508145454Ce325dDbE47a25d4ec3d2311933',
        'network': 'eth',
        'price_at_alert': 0.00000123,
        'score': 85,
        'base_score': 70,
        'momentum_bonus': 15,
        'confidence_score': 90,
        'volume_24h': 500000,
        'volume_6h': 200000,
        'volume_1h': 80000,
        'liquidity': 300000,
        'buys_24h': 1200,
        'sells_24h': 800,
        'buy_ratio': 1.5,
        'total_txns': 2000,
        'age_hours': 12,
        'entry_price': 0.00000123,
        'stop_loss_price': 0.00000123 * 0.90,
        'stop_loss_percent': -10,
        'tp1_price': 0.00000123 * 1.05,
        'tp1_percent': 5,
        'tp2_price': 0.00000123 * 1.10,
        'tp2_percent': 10,
        'tp3_price': 0.00000123 * 1.15,
        'tp3_percent': 15,
        'alert_message': "Texte complet de l'alerte..."
    }

    alert_id = tracker.save_alert(alert_data)
    print(f"Alerte créée avec ID: {alert_id}")

    # Afficher les stats (sera vide au début)
    tracker.print_stats()

    # Récupérer l'historique d'un token
    history = tracker.get_token_history("PEPE")
    print(f"Historique PEPE: {len(history)} alertes")
