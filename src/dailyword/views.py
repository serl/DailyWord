from datetime import date, timedelta

from django.http import HttpRequest, HttpResponse
from django.views import View

from .models import Dictionary
from .rendering import generate_error_image, generate_word_image


class PngResponse(HttpResponse):
    """HttpResponse subclass for PNG images that automatically sets Content-Length."""

    def __init__(self, content: bytes, **kwargs) -> None:
        kwargs["content_type"] = "image/png"
        super().__init__(content, **kwargs)
        self["Content-Length"] = len(content)


class DailyWordImageView(View):
    """
    API endpoint to get the daily word image for a dictionary.

    URL: /api/daily-word/<dictionary_slug>/<width>x<height>/
    Example: /api/daily-word/english-vocabulary/512x256/

    The word changes automatically each day based on a deterministic hash.
    """

    def get(
        self,
        request: HttpRequest,
        dictionary_slug: str,
        width: int,
        height: int,
    ) -> HttpResponse:
        # Clamp dimensions to reasonable values
        width = max(100, min(width, 4096))
        height = max(100, min(height, 4096))

        try:
            dictionary = Dictionary.objects.get(slug=dictionary_slug)
        except Dictionary.DoesNotExist:
            image_data = generate_error_image("Dictionary not found", width, height)
            return PngResponse(image_data)

        today = date.today()
        word = dictionary.get_word_for_date(today)

        if word is None:
            image_data = generate_error_image(
                "No words in this dictionary", width, height
            )
            return PngResponse(image_data)

        yesterday = today - timedelta(days=1)
        yesterday_word = dictionary.get_word_for_date(yesterday)

        image_data = generate_word_image(word, width, height, yesterday_word)

        return PngResponse(image_data)
