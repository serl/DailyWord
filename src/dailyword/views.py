import io
import textwrap
from datetime import date

import cairosvg
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.views import View
from PIL import Image

from .models import Dictionary, Word


def _wrap_text_for_svg(
    text: str, chars_per_line: int, start_y: int, line_height: int
) -> list[dict]:
    """Wrap text and return list of {text, y} dicts for SVG rendering."""
    lines = textwrap.wrap(text, width=chars_per_line)
    return [
        {"text": line, "y": start_y + i * line_height} for i, line in enumerate(lines)
    ]


def generate_word_image(word: Word, width: int, height: int) -> bytes:
    """Generate a grayscale PNG image with all word details using SVG template."""
    # Calculate responsive font sizes based on width
    title_size = max(24, width // 15)
    body_size = max(14, width // 25)
    small_size = max(12, width // 30)
    padding = max(20, width // 20)
    line_height = int(small_size * 1.4)

    # Calculate chars per line for text wrapping
    avg_char_width = small_size * 0.6
    max_text_width = width - 2 * padding - 10
    chars_per_line = max(20, int(max_text_width / avg_char_width))

    # Calculate vertical positions
    y = padding + title_size

    # Calculate inline x position for metadata (after the word)
    word_width_estimate = len(word.word) * title_size * 0.6
    meta_x = padding + word_width_estimate + 10

    def_label_y = y + body_size + 12
    def_start_y = def_label_y + line_height

    definition_lines = _wrap_text_for_svg(
        word.definition, chars_per_line, def_start_y, line_height
    )
    y = definition_lines[-1]["y"] if definition_lines else def_start_y

    example_lines = []
    example_label_y = 0
    if word.example_sentence:
        example_label_y = y + body_size + 12
        example_start_y = example_label_y + line_height
        example_text = f'"{word.example_sentence}"'
        example_lines = _wrap_text_for_svg(
            example_text, chars_per_line, example_start_y, line_height
        )

    # Render SVG template
    svg_content = render_to_string(
        "dailyword/word_image.svg",
        {
            "word": word,
            "width": width,
            "height": height,
            "title_size": title_size,
            "body_size": body_size,
            "small_size": small_size,
            "padding": padding,
            "meta_x": meta_x,
            "def_label_y": def_label_y,
            "definition_lines": definition_lines,
            "example_label_y": example_label_y,
            "example_lines": example_lines,
        },
    )

    # Convert SVG to PNG using cairosvg
    png_data = cairosvg.svg2png(bytestring=svg_content.encode("utf-8"))

    # Convert to grayscale
    img = Image.open(io.BytesIO(png_data))
    grayscale_img = img.convert("L")

    # Save to bytes
    buffer = io.BytesIO()
    grayscale_img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def generate_error_image(message: str, width: int, height: int) -> bytes:
    """Generate a grayscale PNG error image with a 404 message."""
    title_size = max(24, width // 10)
    body_size = max(14, width // 25)

    svg_content = render_to_string(
        "dailyword/error_image.svg",
        {
            "width": width,
            "height": height,
            "title_size": title_size,
            "body_size": body_size,
            "message": message,
        },
    )

    png_data = cairosvg.svg2png(bytestring=svg_content.encode("utf-8"))

    img = Image.open(io.BytesIO(png_data))
    grayscale_img = img.convert("L")

    buffer = io.BytesIO()
    grayscale_img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


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
            return HttpResponse(image_data, content_type="image/png", status=404)

        today = date.today()
        word = dictionary.get_word_for_date(today)

        if word is None:
            image_data = generate_error_image(
                "No words in this dictionary", width, height
            )
            return HttpResponse(image_data, content_type="image/png", status=404)

        image_data = generate_word_image(word, width, height)

        return HttpResponse(image_data, content_type="image/png")
