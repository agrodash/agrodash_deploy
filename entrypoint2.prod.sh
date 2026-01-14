#!/usr/bin/env bash

# Calcula número de workers: (2 * CPU cores) + 1
# Para Railway/containers, usar variável de ambiente ou padrão de 4
WORKERS=${GUNICORN_WORKERS:-4}
THREADS=${GUNICORN_THREADS:-2}

# Executa migrações do banco de dados
python manage.py migrate --noinput &&
python manage.py collectstatic --noinput &

gunicorn core.wsgi:application \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers ${WORKERS} \
        --threads ${THREADS} \
        --worker-class gthread \
        --timeout 120 \
        --keep-alive 5 \
        --max-requests 1000 \
        --max-requests-jitter 50 \
        --access-logfile - \
        --error-logfile - \
        --log-level info
