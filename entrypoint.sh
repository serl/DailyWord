#!/bin/bash
set -e

if [[ $HOME_ASSISTANT_BUILD ]]; then
    echo "Configuring env variables for Home Assistant Supervisor"
    export DATABASE_URL=sqlite:////data/db.sqlite3
    export ALLOWED_HOSTS='*'
fi

django-admin migrate --noinput

exec "$@"
