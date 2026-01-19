#!/bin/bash
set -e

django-admin migrate --noinput

exec "$@"
