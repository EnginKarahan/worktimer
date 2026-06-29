#!/bin/sh
set -e

# Migrationen nur im Web-Container (gunicorn) ausführen – nicht in den
# Celery-/Beat-Containern, die dasselbe Image mit anderem command starten.
case "$1" in
    gunicorn)
        echo "[entrypoint] Wende Datenbank-Migrationen an ..."
        python manage.py migrate --noinput
        ;;
esac

exec "$@"
