# Image Python stable (important)
FROM python:3.12-slim

# Empêche les fichiers .pyc et optimise les logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV PIP_NO_CACHE_DIR=1
ENV PIP_DEFAULT_TIMEOUT=200

# Dossier de travail dans le container
WORKDIR /app

# Installer les dépendances système (utile pour mysqlclient)
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --default-timeout=200 --no-cache-dir -r requirements.txt\
    -i https://pypi.org/simple

# Copier tout le projet
COPY . .

# Commande par défaut (prod)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]