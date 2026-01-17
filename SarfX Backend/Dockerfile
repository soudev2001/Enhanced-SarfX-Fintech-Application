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

# Exposition du port (8087 pour le backend IA SarfX)
ENV PORT 8087
ENV AI_PORT 8087
EXPOSE 8087

# Lancement avec Uvicorn (Serveur ASGI pour FastAPI)
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1