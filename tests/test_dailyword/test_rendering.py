import io

import pytest
from PIL import Image
from syrupy.extensions.image import PNGImageSnapshotExtension

from dailyword.models import Dictionary, Word
from dailyword.rendering import generate_error_image, generate_word_image


@pytest.fixture
def snapshot_png(snapshot):
    return snapshot.use_extension(PNGImageSnapshotExtension)


@pytest.fixture
def dictionary(db):
    return Dictionary.objects.create(
        name="Test Dictionary",
        slug="test-dictionary",
        prompt="test prompt",
    )


@pytest.fixture
def word(dictionary):
    """Create a word with all fields populated."""
    return Word.objects.create(
        dictionary=dictionary,
        word="Ephemeral",
        definition="Lasting for a very short time.",
        example_sentence="The ephemeral beauty of cherry blossoms reminds us to appreciate the moment.",
        pronunciation="ih-FEM-er-uhl",
        part_of_speech="adjective",
    )


@pytest.fixture
def word_minimal(dictionary):
    """Create a word with only required fields."""
    return Word.objects.create(
        dictionary=dictionary,
        word="Test",
        definition="A simple test word.",
    )


@pytest.fixture
def yesterday_word(dictionary):
    """Create a second word to use as yesterday's word."""
    return Word.objects.create(
        dictionary=dictionary,
        word="Serendipity",
        definition="The occurrence of finding pleasant things by chance.",
        example_sentence="It was pure serendipity that they met at the cafe.",
        pronunciation="ser-en-DIP-ih-tee",
        part_of_speech="noun",
    )


class TestGenerateWordImage:
    def test_generates_grayscale_png(self, word):
        image_data = generate_word_image(word, 800, 600)

        img = Image.open(io.BytesIO(image_data))
        assert img.format == "PNG"
        assert img.mode == "L"
        assert img.size == (800, 600)

    def test_works_with_minimal_word(self, word_minimal, snapshot_png):
        image_data = generate_word_image(word_minimal, 512, 256)

        img = Image.open(io.BytesIO(image_data))
        assert img.format == "PNG"
        assert img.mode == "L"
        assert img.size == (512, 256)
        assert image_data == snapshot_png

    def test_with_yesterday_word(self, word, yesterday_word, snapshot_png):
        image_data = generate_word_image(word, 800, 600, yesterday_word)

        img = Image.open(io.BytesIO(image_data))
        assert img.format == "PNG"
        assert img.mode == "L"
        assert img.size == (800, 600)
        assert image_data == snapshot_png


class TestGenerateErrorImage:
    def test_generates_image(self, snapshot_png):
        image_data = generate_error_image("Test error", 800, 600)

        img = Image.open(io.BytesIO(image_data))
        assert img.format == "PNG"
        assert img.mode == "L"
        assert img.size == (800, 600)
        assert image_data == snapshot_png
