# ===========================================
# SarfX Flask Application - Dockerfile
# ===========================================
# Multi-stage build pour optimiser la taille de l'image

# ============ STAGE 1: Builder ============
FROM python:3.12-slim as builder

WORKDIR /app

# Installer les dépendances système pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============ STAGE 2: Production ============
FROM python:3.12-slim as production

# Métadonnées
LABEL maintainer="SarfX Team <dev@sarfx.io>"
LABEL version="2.0"
LABEL description="SarfX Enhanced - Fintech Application"

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r sarfx && useradd -r -g sarfx sarfx

WORKDIR /app

# Installer les dépendances runtime minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copier les dépendances Python depuis le builder
COPY --from=builder /root/.local /home/sarfx/.local

# S'assurer que les scripts Python sont dans le PATH
ENV PATH=/home/sarfx/.local/bin:$PATH

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production \
    PORT=5050

# Copier le code de l'application
COPY --chown=sarfx:sarfx . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs /app/uploads \
    && chown -R sarfx:sarfx /app

# Changer vers l'utilisateur non-root
USER sarfx

# Exposer le port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Commande par défaut (Gunicorn pour production)
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "4", "--threads", "2", \
     "--worker-class", "gthread", "--timeout", "120", "--keep-alive", "5", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--capture-output", "--enable-stdio-inheritance", \
     "run:app"]
