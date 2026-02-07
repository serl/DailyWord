#!/bin/bash
set -e

if [[ $HOME_ASSISTANT_BUILD ]]; then
    echo HELLO HOME ASSISTANT BUILD!
fi

django-admin migrate --noinput

exec "$@"
