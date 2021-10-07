#!/bin/bash

rm -f /tmp/celery_beat.pid
rm -f /tmp/celery_worker.pid


python -m poetry run \
 celery -A app.core beat \
    -l info \
    --pidfile=/tmp/celery_beat.pid  &

python -m poetry run \
 celery -A app.core worker \
    -Q default \
    -E \
    -l info \
    -c ${CELERY_WORKERS:-1} \
    --pidfile=/tmp/celery_worker.pid
