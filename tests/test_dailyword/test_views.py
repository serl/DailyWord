import io
from datetime import date
from unittest.mock import patch

import pytest
from django.test import Client
from PIL import Image

from dailyword.models import Dictionary, Word
from dailyword.views import PngResponse


@pytest.fixture
def client():
    return Client()


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


class TestPngResponse:
    def test_sets_content_type(self):
        response = PngResponse(b"test content")
        assert response["Content-Type"] == "image/png"

    def test_content_length_matches_actual_content(self):
        content = b"x" * 1000
        response = PngResponse(content)
        assert response["Content-Length"] == "1000"


class TestDailyWordImageView:
    def test_returns_image_for_valid_dictionary(self, client, word):
        with patch("dailyword.views.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 1)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            response = client.get("/test-dictionary/512x256/")

        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"
        assert "Content-Length" in response
        assert int(response["Content-Length"]) == len(response.content)

        img = Image.open(io.BytesIO(response.content))
        assert img.format == "PNG"

    def test_returns_grayscale_image(self, client, word):
        with patch("dailyword.views.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 1)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            response = client.get("/test-dictionary/512x256/")

        img = Image.open(io.BytesIO(response.content))
        assert img.mode == "L"

    def test_respects_requested_dimensions(self, client, word):
        with patch("dailyword.views.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 1)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            response = client.get("/test-dictionary/800x600/")

        img = Image.open(io.BytesIO(response.content))
        assert img.size == (800, 600)

    def test_clamps_small_dimensions(self, client, word):
        with patch("dailyword.views.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 1)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            response = client.get("/test-dictionary/10x10/")

        img = Image.open(io.BytesIO(response.content))
        assert img.size == (100, 100)

    def test_clamps_large_dimensions(self, client, word):
        with patch("dailyword.views.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 1)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            response = client.get("/test-dictionary/10000x10000/")

        img = Image.open(io.BytesIO(response.content))
        assert img.size == (4096, 4096)

    def test_dictionary_not_found(self, client, db):
        response = client.get("/nonexistent/512x256/")

        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"
        assert "Content-Length" in response
        assert int(response["Content-Length"]) == len(response.content)

        img = Image.open(io.BytesIO(response.content))
        assert img.format == "PNG"
        assert img.mode == "L"

    def test_empty_dictionary(self, client, dictionary):
        response = client.get("/test-dictionary/512x256/")

        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"
        assert "Content-Length" in response
        assert int(response["Content-Length"]) == len(response.content)

        img = Image.open(io.BytesIO(response.content))
        assert img.format == "PNG"
        assert img.mode == "L"
