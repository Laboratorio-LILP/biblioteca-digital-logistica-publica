import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-in-production")
DEBUG = env("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ── Proxy reverso / subcaminho /Biblioteca (parametrizado; default seguro p/ dev) ──
# Pré-requisito na VM: index.php como proxy transparente (repassa Host + X-Forwarded-*,
# NÃO redirect). Sem as vars do .env (dev local), nada disto altera o comportamento.
USE_X_FORWARDED_HOST = True  # confia no Host público repassado pelo front-controller
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # reconhece HTTPS no proxy
FORCE_SCRIPT_NAME = env("FORCE_SCRIPT_NAME", default=None) or None  # ex.: "/Biblioteca"; "" (dev) → None
CSRF_TRUSTED_ORIGINS = [o for o in env.list("CSRF_TRUSTED_ORIGINS", default=[]) if o.strip()]  # esquema+host públicos; ignora vazios

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "catalog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "portal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "catalog.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "portal.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="nourau"),
        "USER": env("PORTAL_DB_USER", default="portal_reader"),
        "PASSWORD": env("PORTAL_DB_PASSWORD", default="portal_reader_dev"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# STATIC_URL respeita o subcaminho (FORCE_SCRIPT_NAME): {% static %} resolve sob
# /Biblioteca/static/ no público e /static/ no dev local (prefixo vazio).
_script_prefix = (FORCE_SCRIPT_NAME or "").rstrip("/")
STATIC_URL = f"{_script_prefix}/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Cookies presos ao subcaminho quando atrás do proxy (não vazam p/ outros apps do host).
if FORCE_SCRIPT_NAME:
    SESSION_COOKIE_PATH = FORCE_SCRIPT_NAME
    CSRF_COOKIE_PATH = FORCE_SCRIPT_NAME
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URL base do Nou-Rau para downloads e links internos
NOURAU_BASE_URL = env("NOURAU_SITE_URL", default="http://localhost:8080")
NOURAU_ARCHIVE_DIR = env("NOURAU_ARCHIVE_DIR", default="/nourau/archive")

# Itens por página nos resultados de busca
SEARCH_RESULTS_PER_PAGE = 20

# Segurança. Flags que EXIGEM HTTPS ficam sob SECURE_SSL (separado de DEBUG),
# para que DEBUG=false funcione na VM de homologação (somente HTTP/:80).
# Em produção com TLS (Prodesp): SECURE_SSL=true.
SECURE_SSL = env.bool("SECURE_SSL", default=False)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
if SECURE_SSL:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
if not DEBUG:

    # Content-Security-Policy via django-csp.
    # Inserido após SecurityMiddleware para que CSP atue antes do whitenoise
    # processar arquivos estáticos. Não ativado em DEBUG para evitar que
    # ferramentas locais (DevTools, painel de extensões) sejam bloqueadas.
    MIDDLEWARE.insert(1, "csp.middleware.CSPMiddleware")

    # Permitir apenas o próprio domínio por padrão.
    CSP_DEFAULT_SRC = ("'self'",)

    # Imagens: own + data URIs + domínios oficiais Governo SP.
    CSP_IMG_SRC = (
        "'self'",
        "data:",
        "https://saopaulo.sp.gov.br",
        "https://compras.sp.gov.br",
    )

    # Fontes: own + Google Fonts (Roboto, conforme Manual GESP v1.6).
    CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")

    # Estilos: own + Google Fonts CSS. 'unsafe-inline' por compatibilidade
    # com pequenos style="" inline em formulários (CSRF tokens etc.); pode
    # ser endurecido para nonces em iteração futura.
    CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")

    # Scripts: SOMENTE do próprio domínio. main.js usa apenas
    # addEventListener (zero inline handlers), permitindo que NÃO haja
    # 'unsafe-inline' aqui.
    CSP_SCRIPT_SRC = ("'self'",)

    # Conexões XHR/fetch: apenas próprio domínio.
    CSP_CONNECT_SRC = ("'self'",)

    # Fronteiras de mídia, frames, objetos: bloqueados por padrão.
    CSP_FRAME_ANCESTORS = ("'none'",)
    CSP_BASE_URI = ("'self'",)
    CSP_FORM_ACTION = ("'self'",)
