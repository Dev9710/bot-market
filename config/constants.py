"""
Constantes globales du Scanner V3

Valeurs qui ne changent jamais ou très rarement.
"""

# ============================================
# COOLDOWNS RÈGLES 4 ET 5
# ============================================

# Cooldown pour Règle 4 (même token, nouvelle alerte)
COOLDOWN_REGLE_4 = 3600  # 1 heure en secondes

# Cooldown pour Règle 5 (réapparition token)
COOLDOWN_REGLE_5 = 86400  # 24 heures en secondes

# ============================================
# LIMITES LIQUIDITÉ
# ============================================

# Seuil max de liquidité (au-delà = trop gros, pas memecoin)
MAX_LIQUIDITY_THRESHOLD = 10000000  # 10M USD
