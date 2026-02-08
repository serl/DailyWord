#!/bin/bash
set -e

if [[ $HOME_ASSISTANT_BUILD ]]; then
    echo "Configuring env variables for Home Assistant Supervisor"
    export DATABASE_URL=sqlite:////data/db.sqlite3
    export ALLOWED_HOSTS='*'

    eval python -c "import json; options = json.loads(open('/data/options.json').read()); print('\n'.join(f'export {key.upper()}={value}' for key, value in options.items()))"
fi

django-admin migrate --noinput

exec "$@"
