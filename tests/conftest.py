import os

os.environ["DJANGO_DEBUG"] = "False"

import pytest
from django.conf import settings
from django.utils import translation


@pytest.fixture(autouse=True)
def set_test_settings(settings):
    settings.STORAGES |= {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
    settings.TEMPLATES = [
        template_conf
        | {
            "OPTIONS": template_conf["OPTIONS"]
            | {
                # Necessary for django-coverage-plugin
                "debug": True,
            },
        }
        for template_conf in settings.TEMPLATES
    ]


@pytest.fixture(autouse=True)
def switch_language_to_default():
    """
    When Django sets the language using HTTP headers, it does it on a thread level.

    This will ensure that each test runs with the relevant language, independently of what happened just before.
    """
    translation.activate(settings.LANGUAGE_CODE)


@pytest.fixture(autouse=True)
def clear_contenttype_cache():
    """
    Clear the content type cache before each test.
    Django caches the content types in memory, and this clashes happily with the tests that assert a certain number of queries.
    By clearing the cache, we ensure that all the tests start with the same state.
    """
    from django.contrib.contenttypes.models import ContentType  # noqa: PLC0415

    ContentType.objects.clear_cache()
