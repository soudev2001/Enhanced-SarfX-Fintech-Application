FROM python:3.9-slim

# Configuration pour les logs
ENV PYTHONUNBUFFERED True

# Répertoire de travail
WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Exposition du port (8080 pour Cloud Run par défaut, ou autre)
ENV PORT 8080
EXPOSE 8080

# Lancement avec Gunicorn (Serveur de prod)
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 run:app