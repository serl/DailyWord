from django.urls import get_script_prefix
from whitenoise.storage import CompressedManifestStaticFilesStorage


class IngressAwareStaticFilesStorage(CompressedManifestStaticFilesStorage):
    def url(self, name):
        base_url = super().url(name)
        prefix = get_script_prefix().rstrip("/")
        if prefix:
            return prefix + base_url
        return base_url
