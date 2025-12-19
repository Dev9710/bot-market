"""
Script pour telecharger la base de donnees depuis Railway via SSH
"""
import subprocess
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("Telechargement de la base de donnees depuis Railway...")

try:
    # Utiliser railway ssh pour exécuter cat et rediriger vers un fichier
    # Sur Windows, utiliser cmd.exe pour exécuter le fichier .cmd
    result = subprocess.run(
        ["cmd.exe", "/c", "railway", "ssh", "--", "cat", "/app/alerts_history.db"],
        capture_output=True,
        check=True
    )

    # Écrire les données binaires dans le fichier
    with open("alerts_railway.db", "wb") as f:
        f.write(result.stdout)

    print(f"OK - Base de donnees telechargee : {len(result.stdout)} octets")

    # Verifier que c'est bien une DB SQLite
    import sqlite3
    conn = sqlite3.connect("alerts_railway.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alerts")
    count = cursor.fetchone()[0]
    print(f"Nombre d'alertes : {count}")
    conn.close()

except subprocess.CalledProcessError as e:
    print(f"ERREUR lors du telechargement : {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERREUR : {e}")
    sys.exit(1)
