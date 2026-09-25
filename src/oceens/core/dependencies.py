"""Objets applicatifs partages par tous les routeurs.

`templates` etait une variable locale de `create_app()`, capturee par
fermeture par les routes. La sortir ici est ce qui rend le decoupage en
modules possible.
"""

import logging
from pathlib import Path

from fastapi.templating import Jinja2Templates

# Moteur de templates Jinja2 partagé par toutes les routes qui rendent du HTML
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(PACKAGE_ROOT / "templates"))
# Ne pas trier les clés JSON (préserver l'ordre voulu dans les templates)
templates.env.policies["json.dumps_kwargs"] = {"sort_keys": False}

# Logger partagé : on réutilise celui d'uvicorn pour hériter de son format/handlers
logger = logging.getLogger("uvicorn")
logger.level=logging.DEBUG
