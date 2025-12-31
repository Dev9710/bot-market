#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply portfolio table migration to alerts database
"""
import sqlite3
import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Find the database
DB_PATH = os.getenv("DB_PATH")
if not DB_PATH:
    if os.path.exists("alerts_tracker.db"):
        DB_PATH = "alerts_tracker.db"
    elif os.path.exists("alerts_history.db"):
        DB_PATH = "alerts_history.db"
    else:
        print("ERROR: Database not found!")
        exit(1)

print(f"Using database: {DB_PATH}")

# Read migration SQL
with open("migrations/add_portfolio_table.sql", "r") as f:
    migration_sql = f.read()

# Apply migration
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Execute migration (handles multiple statements)
    cursor.executescript(migration_sql)

    conn.commit()
    print("SUCCESS: Portfolio table created successfully!")

    # Verify table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='portfolio'")
    if cursor.fetchone():
        print("SUCCESS: Verification - portfolio table exists")

        # Show table structure
        cursor.execute("PRAGMA table_info(portfolio)")
        columns = cursor.fetchall()
        print(f"\nPortfolio table structure ({len(columns)} columns):")
        for col in columns:
            print(f"   - {col[1]}: {col[2]}")
    else:
        print("ERROR: Verification failed - table not found")

    conn.close()

except Exception as e:
    print(f"ERROR: Error applying migration: {e}")
    exit(1)
