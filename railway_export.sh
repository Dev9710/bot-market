#!/bin/bash
# Script a executer sur Railway pour exporter la DB
sqlite3 /app/alerts_history.db .dump > /tmp/alerts_dump.sql
echo "Export termine - Telechargez avec: railway ssh -- cat /tmp/alerts_dump.sql > alerts_dump.sql"
