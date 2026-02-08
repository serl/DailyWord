#!/bin/bash
set -e

if [[ $HOME_ASSISTANT_BUILD ]]; then
    echo "Configuring env variables for Home Assistant Supervisor"
    export DATABASE_URL=sqlite:////data/db.sqlite3
    export ALLOWED_HOSTS='*'

    get_option() {
        python -c "import json; options = json.loads(open('/data/options.json').read()); print(options.get('$1', ''))"
    }

    export OPENROUTER_API_KEY="$(get_option "openrouter_api_key")"
    export OPENROUTER_TEXT_MODEL="$(get_option "openrouter_text_model")"
fi

django-admin migrate --noinput

if [[ $HOME_ASSISTANT_BUILD ]]; then
    fixture_file=/share/dailyword.json
    if [[ -r $fixture_file ]]; then
        echo "Loading data from $fixture_file"
        django-admin loaddata --format=json - <"$fixture_file"
    fi
fi

exec "$@"
