"""
Verifie et met a jour le schema de la base de donnees
pour un backtesting reel et fiable
"""

import sqlite3
import os

DB_LOCAL = r"c:\Users\ludo_\Documents\projets\owner\bot-market\alerts_history.db"

def get_current_schema():
    """Recupere le schema actuel de la table alerts"""
    conn = sqlite3.connect(DB_LOCAL)
    cursor = conn.execute("PRAGMA table_info(alerts)")
    columns = cursor.fetchall()
    conn.close()

    return {col[1]: col[2] for col in columns}  # {nom: type}

def get_required_columns_for_backtesting():
    """Definit TOUTES les colonnes necessaires pour un backtesting REEL"""

    return {
        # === IDENTIFICATION ===
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'timestamp': 'TEXT',
        'created_at': 'TEXT',

        # === TOKEN INFO ===
        'token_name': 'TEXT',
        'token_symbol': 'TEXT',
        'token_address': 'TEXT',
        'pool_address': 'TEXT',  # CRITIQUE pour fetch prix actuel
        'network': 'TEXT',

        # === PRIX (CRITIQUE POUR BACKTESTING) ===
        'price_at_alert': 'REAL',  # Prix au moment de l'alerte
        'entry_price': 'REAL',     # Prix d'entree recommande

        # === TP/SL (CRITIQUE) ===
        'stop_loss_price': 'REAL',
        'stop_loss_percent': 'REAL',
        'tp1_price': 'REAL',
        'tp1_percent': 'REAL',
        'tp2_price': 'REAL',
        'tp2_percent': 'REAL',
        'tp3_price': 'REAL',
        'tp3_percent': 'REAL',

        # === TRACKING PRIX (NOUVEAU - CRITIQUE!) ===
        'price_1h_after': 'REAL',      # Prix 1h apres alerte
        'price_2h_after': 'REAL',      # Prix 2h apres
        'price_4h_after': 'REAL',      # Prix 4h apres
        'price_24h_after': 'REAL',     # Prix 24h apres
        'price_max_reached': 'REAL',   # Prix maximum atteint
        'price_min_reached': 'REAL',   # Prix minimum atteint
        'time_to_tp1': 'REAL',         # Temps en heures pour atteindre TP1 (NULL si pas atteint)
        'time_to_tp2': 'REAL',         # Temps pour TP2
        'time_to_tp3': 'REAL',         # Temps pour TP3
        'time_to_sl': 'REAL',          # Temps pour SL
        'highest_tp_reached': 'TEXT',  # TP1, TP2, TP3, ou NONE
        'sl_hit': 'INTEGER',           # 1 si SL atteint, 0 sinon

        # === RESULTAT FINAL (NOUVEAU - CRITIQUE!) ===
        'final_outcome': 'TEXT',       # WIN_TP3, WIN_TP2, WIN_TP1, LOSS_SL, ONGOING
        'final_gain_percent': 'REAL',  # Gain/perte final en %
        'final_gain_usd': 'REAL',      # Gain/perte en USD (si position connue)
        'is_closed': 'INTEGER',        # 1 si trade cloture, 0 si en cours
        'closed_at': 'TEXT',           # Date de cloture

        # === SCORING ===
        'score': 'INTEGER',
        'base_score': 'INTEGER',
        'momentum_bonus': 'INTEGER',
        'confidence_score': 'INTEGER',
        'tier': 'TEXT',  # ULTRA_HIGH, HIGH, MEDIUM, LOW, VERY_LOW

        # === METRIQUES MARCHE ===
        'volume_24h': 'REAL',
        'volume_6h': 'REAL',
        'volume_1h': 'REAL',
        'liquidity': 'REAL',
        'buys_24h': 'INTEGER',
        'sells_24h': 'INTEGER',
        'buy_ratio': 'REAL',
        'total_txns': 'INTEGER',
        'age_hours': 'REAL',

        # === ACCELERATION ===
        'volume_acceleration_1h_vs_6h': 'REAL',
        'volume_acceleration_6h_vs_24h': 'REAL',
        'velocite_pump': 'REAL',
        'type_pump': 'TEXT',

        # === METADATA ===
        'alert_message': 'TEXT',
        'decision_tp_tracking': 'TEXT',
        'temps_depuis_alerte_precedente': 'REAL',
        'is_alerte_suivante': 'INTEGER',
        'version': 'TEXT'
    }

def compare_schemas(current, required):
    """Compare schema actuel vs requis"""

    missing = []
    existing = []

    for col_name, col_type in required.items():
        if col_name in current:
            existing.append(col_name)
        else:
            missing.append((col_name, col_type))

    return existing, missing

def generate_migration_sql(missing_columns):
    """Genere le SQL pour ajouter les colonnes manquantes"""

    sql_statements = []

    for col_name, col_type in missing_columns:
        # Extraire juste le type sans les contraintes
        base_type = col_type.split()[0]
        sql = f"ALTER TABLE alerts ADD COLUMN {col_name} {base_type};"
        sql_statements.append(sql)

    return sql_statements

def apply_migrations(sql_statements):
    """Applique les migrations SQL"""

    if not sql_statements:
        print("Aucune migration necessaire - schema deja complet!")
        return True

    conn = sqlite3.connect(DB_LOCAL)

    try:
        for i, sql in enumerate(sql_statements, 1):
            print(f"  [{i}/{len(sql_statements)}] {sql}")
            conn.execute(sql)

        conn.commit()
        print(f"\nOK {len(sql_statements)} colonnes ajoutees avec succes!")
        return True

    except Exception as e:
        print(f"\nERREUR lors de la migration: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

def generate_database_documentation():
    """Genere la documentation du schema"""

    required = get_required_columns_for_backtesting()

    doc = []
    doc.append("=" * 80)
    doc.append("SCHEMA DE LA BASE DE DONNEES - BACKTESTING COMPLET")
    doc.append("=" * 80)
    doc.append("")

    categories = {
        'IDENTIFICATION': ['id', 'timestamp', 'created_at'],
        'TOKEN INFO': ['token_name', 'token_symbol', 'token_address', 'pool_address', 'network'],
        'PRIX': ['price_at_alert', 'entry_price'],
        'TP/SL': ['stop_loss_price', 'stop_loss_percent', 'tp1_price', 'tp1_percent',
                  'tp2_price', 'tp2_percent', 'tp3_price', 'tp3_percent'],
        'TRACKING PRIX (NOUVEAU)': ['price_1h_after', 'price_2h_after', 'price_4h_after',
                                     'price_24h_after', 'price_max_reached', 'price_min_reached',
                                     'time_to_tp1', 'time_to_tp2', 'time_to_tp3', 'time_to_sl',
                                     'highest_tp_reached', 'sl_hit'],
        'RESULTAT FINAL (NOUVEAU)': ['final_outcome', 'final_gain_percent', 'final_gain_usd',
                                      'is_closed', 'closed_at'],
        'SCORING': ['score', 'base_score', 'momentum_bonus', 'confidence_score', 'tier'],
        'METRIQUES MARCHE': ['volume_24h', 'volume_6h', 'volume_1h', 'liquidity',
                             'buys_24h', 'sells_24h', 'buy_ratio', 'total_txns', 'age_hours'],
        'ACCELERATION': ['volume_acceleration_1h_vs_6h', 'volume_acceleration_6h_vs_24h',
                         'velocite_pump', 'type_pump'],
        'METADATA': ['alert_message', 'decision_tp_tracking', 'temps_depuis_alerte_precedente',
                     'is_alerte_suivante', 'version']
    }

    for category, columns in categories.items():
        doc.append(f"\n{category}:")
        doc.append("-" * 80)
        for col in columns:
            if col in required:
                col_type = required[col]
                doc.append(f"  {col:<35} {col_type}")

    doc.append("")
    doc.append("=" * 80)
    doc.append("TOTAL: {} colonnes".format(len(required)))
    doc.append("=" * 80)

    return "\n".join(doc)

def verify_critical_columns():
    """Verifie que toutes les colonnes critiques sont presentes"""

    critical_for_backtesting = [
        'pool_address',          # Pour fetch prix actuel
        'entry_price',           # Prix entry
        'tp1_price', 'tp2_price', 'tp3_price',  # TP
        'stop_loss_price',       # SL
        'price_1h_after',        # Tracking 1h
        'price_24h_after',       # Tracking 24h
        'price_max_reached',     # Prix max
        'final_outcome',         # Resultat
        'final_gain_percent',    # Gain %
        'is_closed',             # Statut
    ]

    current = get_current_schema()

    missing_critical = [col for col in critical_for_backtesting if col not in current]

    return missing_critical

if __name__ == '__main__':
    print("=" * 80)
    print("VERIFICATION ET MISE A JOUR DU SCHEMA DE LA BASE DE DONNEES")
    print("=" * 80)
    print()

    # 1. Schema actuel
    print("[1/5] Analyse du schema actuel...")
    current = get_current_schema()
    print(f"      OK {len(current)} colonnes actuelles")
    print()

    # 2. Schema requis
    print("[2/5] Definition du schema requis pour backtesting reel...")
    required = get_required_columns_for_backtesting()
    print(f"      OK {len(required)} colonnes requises")
    print()

    # 3. Comparaison
    print("[3/5] Comparaison des schemas...")
    existing, missing = compare_schemas(current, required)
    print(f"      Existantes: {len(existing)}")
    print(f"      Manquantes: {len(missing)}")
    print()

    if missing:
        print("Colonnes manquantes:")
        for col_name, col_type in missing:
            print(f"  - {col_name} ({col_type})")
        print()

    # 4. Migration
    print("[4/5] Application des migrations...")
    if missing:
        sql_statements = generate_migration_sql(missing)
        success = apply_migrations(sql_statements)

        if not success:
            print("ERREUR: Migration echouee!")
            exit(1)
    else:
        print("      Aucune migration necessaire - schema deja complet!")
    print()

    # 5. Verification finale
    print("[5/5] Verification finale...")
    missing_critical = verify_critical_columns()

    if missing_critical:
        print(f"  (!!) ATTENTION: {len(missing_critical)} colonnes critiques manquantes:")
        for col in missing_critical:
            print(f"      - {col}")
    else:
        print("  OK Toutes les colonnes critiques sont presentes!")
    print()

    # Documentation
    print("=" * 80)
    print("GENERATION DE LA DOCUMENTATION")
    print("=" * 80)
    print()

    doc = generate_database_documentation()

    # Sauvegarder
    with open('DATABASE_SCHEMA.md', 'w', encoding='utf-8') as f:
        f.write(doc)

    print("OK Documentation sauvegardee dans DATABASE_SCHEMA.md")
    print()

    # Afficher resume
    print(doc)
    print()

    print("=" * 80)
    print("PROCHAINES ETAPES")
    print("=" * 80)
    print()
    print("1. Schema de la base de donnees: OK (mise a jour)")
    print("2. Modifier le code du bot pour enregistrer les nouvelles colonnes")
    print("3. Creer un script de tracking pour mettre a jour price_1h_after, etc.")
    print("4. Laisser tourner le bot quelques jours")
    print("5. Lancer le backtesting REEL avec les vraies donnees")
    print()
    print("=" * 80)
