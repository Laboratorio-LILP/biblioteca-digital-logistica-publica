FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências do sistema para psycopg2
RUN apt-get update && apt-get install -y \
        libpq-dev \
        gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python do lockfile (fonte única; sem lista duplicada)
COPY pyproject.toml requirements.lock /app/
RUN pip install --no-cache-dir -r requirements.lock

# Copiar código do portal
COPY portal/ /app/

# Coletar arquivos estáticos
RUN DJANGO_SECRET_KEY=build-placeholder python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "portal.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
