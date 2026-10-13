FROM python:3.12-slim

# uv installe les dépendances depuis uv.lock : mêmes versions que sur un poste
# de développement, sans résolution au moment du build.
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Les dépendances d'abord, sans le projet : cette couche reste en cache tant
# que le lock ne change pas, et une modification du code ne la refait pas.
COPY pyproject.toml uv.lock .python-version README.md ./
RUN uv sync --frozen --no-install-project

# Tout le code applicatif vit sous src/oceens : un seul COPY, templates,
# fichiers statiques et CSV de seed compris.
COPY src ./src
RUN uv sync --frozen

# Le répertoire database/ est créé automatiquement par database.py au démarrage.
# Monter /app/database comme volume pour persister la base SQLite entre les redémarrages.
# Le fichier .env ne doit PAS être copié dans l'image : fournir les secrets via
# --env-file .env au lancement (docker run) ou via les variables d'environnement.

# `oceens` est le point d'entrée installé avec le paquet (uvicorn sur 0.0.0.0:8000).
# App Service termine TLS avant le conteneur. Uvicorn doit croire son proxy
# pour construire les liens HTTPS. Le daemon partage la base du serveur web.
ENV FORWARDED_ALLOW_IPS="*" \
    RUN_SUMMARIES_DAEMON=1
EXPOSE 8000

# Le déploiement attend une réponse de cette révision précise.
ARG REVISION=unknown
ENV REVISION=$REVISION

CMD ["oceens"]
