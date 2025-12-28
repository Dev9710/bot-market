#!/usr/bin/env python3
"""Corrige l'encodage du fichier JSON exporté de Railway."""

import sys

input_file = "alerts_railway_export.json"
output_file = "alerts_railway_export_utf8.json"

print(f"Conversion de {input_file} (UTF-16) vers {output_file} (UTF-8)...")

try:
    # Lire en UTF-16
    with open(input_file, 'r', encoding='utf-16') as f:
        content = f.read()

    # Écrire en UTF-8
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Conversion réussie!")
    print(f"📁 Fichier corrigé: {output_file}")
    print(f"\n💡 Utilisez maintenant:")
    print(f"   python import_json_to_sqlite.py {output_file}")

except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)
