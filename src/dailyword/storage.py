from django.urls import get_script_prefix
from whitenoise.storage import CompressedManifestStaticFilesStorage


class ScriptPrefixAwareCompressedManifestStaticFilesStorage(
    CompressedManifestStaticFilesStorage
):
    def url(self, name, force=False):
        base_url = super().url(name, force=force)
        prefix = get_script_prefix().rstrip("/")
        if prefix:
            return prefix + base_url
        return base_url
