import io
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import Word

FONTS_DIR = Path(__file__).parent / "fonts"

# Colors for grayscale mode "L"
WHITE = 255
BLACK = 0
DARK_GRAY = 40
MEDIUM_GRAY = 80
LIGHT_GRAY = 120
DIVIDER_GRAY = 180


@lru_cache(maxsize=16)
def _load_font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(FONTS_DIR / filename), size)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels using actual font metrics."""
    words = text.split()
    if not words:
        return []

    lines: list[str] = []
    current_line = words[0]

    for word in words[1:]:
        test_line = f"{current_line} {word}"
        bbox = font.getbbox(test_line)
        if bbox[2] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def generate_word_image(
    word: Word,
    width: int,
    height: int,
    yesterday_word: Word | None = None,
) -> bytes:
    """Generate a grayscale PNG image with word details using Pillow."""
    img = Image.new("L", (width, height), WHITE)
    draw = ImageDraw.Draw(img)

    # Responsive sizing
    title_size = max(24, width // 15)
    body_size = max(14, width // 25)
    small_size = max(12, width // 30)
    padding = max(20, width // 20)
    max_text_width = width - 2 * padding

    title_font = _load_font(bold=True, size=title_size)
    small_font = _load_font(bold=False, size=small_size)
    small_bold_font = _load_font(bold=True, size=small_size)
    label_font = _load_font(bold=True, size=body_size)

    y = padding

    # Title line: WORD  (part_of_speech)  /pronunciation/
    title_text = word.word.upper()
    draw.text((padding, y), title_text, font=title_font, fill=BLACK)
    title_bbox = title_font.getbbox(title_text)
    meta_x = padding + title_bbox[2] + 10

    meta_parts = []
    if word.part_of_speech:
        meta_parts.append(f"({word.part_of_speech})")
    if word.pronunciation:
        meta_parts.append(f"/{word.pronunciation}/")
    if meta_parts:
        meta_text = "  ".join(meta_parts)
        # Vertically align metadata with title baseline
        meta_y = y + (title_bbox[3] - small_font.getbbox(meta_text)[3])
        draw.text((meta_x, meta_y), meta_text, font=small_font, fill=MEDIUM_GRAY)

    y += title_bbox[3] + body_size

    # Definition
    draw.text((padding, y), "Definition:", font=label_font, fill=DARK_GRAY)
    y += int(body_size * 1.5)

    for line in _wrap_text(word.definition, small_font, max_text_width):
        draw.text((padding, y), line, font=small_font, fill=DARK_GRAY)
        y += int(small_size * 1.4)

    # Example sentence
    if word.example_sentence:
        y += body_size
        draw.text((padding, y), "Example:", font=label_font, fill=DARK_GRAY)
        y += int(body_size * 1.5)

        example_text = f'"{word.example_sentence}"'
        for line in _wrap_text(example_text, small_font, max_text_width):
            draw.text((padding, y), line, font=small_font, fill=LIGHT_GRAY)
            y += int(small_size * 1.4)

    # Yesterday's word section
    if yesterday_word:
        y += body_size
        # Divider line
        draw.line([(padding, y), (width - padding, y)], fill=DIVIDER_GRAY, width=1)
        y += int(small_size * 0.8)

        yesterday_title = f"Yesterday: {yesterday_word.word.upper()}"
        draw.text((padding, y), yesterday_title, font=small_bold_font, fill=MEDIUM_GRAY)
        y += int(small_size * 1.4)

        for line in _wrap_text(yesterday_word.definition, small_font, max_text_width):
            draw.text((padding, y), line, font=small_font, fill=LIGHT_GRAY)
            y += int(small_size * 1.4)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def generate_error_image(message: str, width: int, height: int) -> bytes:
    """Generate a grayscale PNG error image."""
    img = Image.new("L", (width, height), WHITE)
    draw = ImageDraw.Draw(img)

    title_size = max(24, width // 10)
    body_size = max(14, width // 25)

    title_font = _load_font(bold=True, size=title_size)
    message_font = _load_font(bold=False, size=body_size)

    # Center "404" vertically
    title_text = "404"
    title_bbox = title_font.getbbox(title_text)
    title_x = (width - title_bbox[2]) // 2
    title_y = height // 3

    draw.text((title_x, title_y), title_text, font=title_font, fill=BLACK)

    # Center message below
    msg_bbox = message_font.getbbox(message)
    msg_x = (width - msg_bbox[2]) // 2
    msg_y = title_y + title_bbox[3] + body_size

    draw.text((msg_x, msg_y), message, font=message_font, fill=MEDIUM_GRAY)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()
