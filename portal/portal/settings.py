from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)

# DEBUG só liga quando pedido (DJANGO_DEBUG=true no .env de desenvolvimento).
# Ausente vale false: homologação e produção não podem depender de alguém
# lembrar de desligar.
DEBUG = env.bool("DJANGO_DEBUG", default=False)

# Chave secreta SEM padrão conhecido. Fora do desenvolvimento a ausência derruba
# o boot — é o mesmo tratamento que o compose dá às senhas do banco. Em
# desenvolvimento sem chave, uma aleatória por processo (o portal não tem
# sessão nem formulário POST; nada depende da chave persistir).
SECRET_KEY = env("DJANGO_SECRET_KEY", default="")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY não definida. Fora do modo de desenvolvimento o portal só sobe com chave "
            "própria: gere uma com "
            "`python -c \"from django.core.management.utils import get_random_secret_key as g; print(g())\"` "
            "e grave em DJANGO_SECRET_KEY no .env (ver .env.example)."
        )
    SECRET_KEY = "dev-" + get_random_secret_key()
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ── Proxy reverso / subcaminho /Biblioteca (parametrizado; default seguro p/ dev) ──
# Pré-requisito na VM: index.php como proxy transparente (repassa Host + X-Forwarded-*,
# NÃO redirect). Sem as vars do .env (dev local), nada disto altera o comportamento.
USE_X_FORWARDED_HOST = True  # confia no Host público repassado pelo front-controller
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # reconhece HTTPS no proxy
FORCE_SCRIPT_NAME = env("FORCE_SCRIPT_NAME", default=None) or None  # ex.: "/Biblioteca"; "" (dev) → None
# CSRF_TRUSTED_ORIGINS: esquema+host públicos; ignora entradas vazias.
CSRF_TRUSTED_ORIGINS = [o for o in env.list("CSRF_TRUSTED_ORIGINS", default=[]) if o.strip()]

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
        "PASSWORD": env("PORTAL_DB_PASSWORD", default="placeholder-set-PORTAL_DB_PASSWORD"),
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
SEARCH_RESULTS_PER_PAGE = 10

# Registro (log) na saída do contêiner — é o que a TI vê com `docker compose
# logs portal`. Sem isto, com DEBUG=false o Django só tentaria mail_admins e um
# erro 500 em homologação não deixava rastro nenhum (achado F2-01, 23/09/2026).
#   django.request  WARNING: 400/404 (uma linha) e 500 (com a exceção)
#   django.security WARNING: host não permitido, CSRF etc.
#   catalog         INFO:    avisos do portal (ex.: busca sem acento degradada)
# A linha traz método, caminho e status; não traz corpo de requisição nem
# cookies. Com DEBUG=false a exceção também não traz o dump de settings.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "portal": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "portal"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "catalog": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

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
