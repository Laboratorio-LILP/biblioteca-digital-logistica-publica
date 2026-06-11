"""Settings stub para preview offline (sem Docker, sem PostgreSQL).

Usado exclusivamente por tools/preview_render.py — inicializa o Django
como template engine para renderizar os templates do portal em HTML
estático. NÃO conecta a banco de dados.

NÃO usar em produção.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "preview-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "catalog",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "portal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

# Engine dummy — qualquer query lança erro. O preview só usa
# render_to_string() com contexto mock, então as queries não são
# executadas. A urlconf importa views/models, mas isso é só carga
# de classes — não dispara queries.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.dummy",
    },
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Variáveis usadas pelas views (não chamadas no preview, mas precisam
# existir para que settings.py não quebre na importação).
NOURAU_BASE_URL = "http://localhost:8080"
NOURAU_ARCHIVE_DIR = "/tmp/nourau-archive"
SEARCH_RESULTS_PER_PAGE = 10
