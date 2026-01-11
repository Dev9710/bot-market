"""
Cree la table alerts dans PostgreSQL Railway avec TOUTES les colonnes
"""

import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("[SKIP] DATABASE_URL not found - Running locally")
    exit(0)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("=" * 80)
    print("CREATION TABLE ALERTS DANS POSTGRESQL")
    print("=" * 80)
    print()

    # Creer la table avec TOUTES les colonnes (schema complet)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            -- Identification
            id SERIAL PRIMARY KEY,
            timestamp TEXT,
            created_at TEXT,

            -- Token Info
            token_name TEXT,
            token_symbol TEXT,
            token_address TEXT,
            pool_address TEXT,
            network TEXT,

            -- Prix
            price_at_alert REAL,
            entry_price REAL,

            -- TP/SL
            stop_loss_price REAL,
            stop_loss_percent REAL,
            tp1_price REAL,
            tp1_percent REAL,
            tp2_price REAL,
            tp2_percent REAL,
            tp3_price REAL,
            tp3_percent REAL,

            -- Tracking Prix (NOUVEAU)
            price_1h_after REAL,
            price_2h_after REAL,
            price_4h_after REAL,
            price_24h_after REAL,
            price_max_reached REAL,
            price_min_reached REAL,
            time_to_tp1 REAL,
            time_to_tp2 REAL,
            time_to_tp3 REAL,
            time_to_sl REAL,
            highest_tp_reached TEXT,
            sl_hit INTEGER,

            -- Resultat Final (NOUVEAU)
            final_outcome TEXT,
            final_gain_percent REAL,
            final_gain_usd REAL,
            is_closed INTEGER DEFAULT 0,
            closed_at TEXT,

            -- Scoring
            score INTEGER,
            base_score INTEGER,
            momentum_bonus INTEGER,
            confidence_score INTEGER,
            tier TEXT,

            -- Metriques Marche
            volume_24h REAL,
            volume_6h REAL,
            volume_1h REAL,
            liquidity REAL,
            buys_24h INTEGER,
            sells_24h INTEGER,
            buy_ratio REAL,
            total_txns INTEGER,
            age_hours REAL,

            -- Acceleration
            volume_acceleration_1h_vs_6h REAL,
            volume_acceleration_6h_vs_24h REAL,
            velocite_pump REAL,
            type_pump TEXT,

            -- Metadata
            alert_message TEXT,
            decision_tp_tracking TEXT,
            temps_depuis_alerte_precedente REAL,
            is_alerte_suivante INTEGER,
            version TEXT
        )
    """)

    conn.commit()

    print("OK Table 'alerts' creee avec succes!")
    print()

    # Verifier le nombre de colonnes
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'alerts'
    """)

    col_count = cursor.fetchone()[0]
    print(f"Nombre de colonnes: {col_count}")
    print()
    print("=" * 80)
    print("READY FOR PRICE TRACKING!")
    print("=" * 80)

    conn.close()

except Exception as e:
    print(f"ERREUR: {e}")
    exit(1)
