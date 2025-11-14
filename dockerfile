FROM python:3.11-slim

WORKDIR /app

# Copier le bot et la configuration
COPY alerte.py ./alerte.py
COPY config_tokens.json ./config_tokens.json

# Dépendances
RUN pip install --no-cache-dir requests

# Empêche Python de bufferiser les logs
ENV PYTHONUNBUFFERED=1

# Commande par défaut (dashboard actif)
CMD ["python", "alerte.py"]
