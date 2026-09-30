FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Mensagens de log com acento saem legíveis (sem \xe1) no stdout do contêiner
ENV PYTHONIOENCODING=utf-8

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

# Acesso e erros na saída do contêiner (docker compose logs portal): sem isto o
# gunicorn não registra requisição nenhuma e um 500 em homologação passa em silêncio.
CMD ["gunicorn", "portal.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", \
     "--access-logfile", "-", "--error-logfile", "-"]
