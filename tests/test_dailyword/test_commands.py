from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from dailyword.models import Dictionary, Word
from dailyword.services.openrouter import (
    OpenRouterError,
    WordDefinition,
)


@pytest.fixture
def dictionary(db):
    return Dictionary.objects.create(
        name="Test Dictionary",
        slug="test-dictionary",
        prompt="vocabulary words related to testing at beginner level",
    )


@pytest.fixture
def word(dictionary):
    return Word.objects.create(
        dictionary=dictionary,
        word="Existing",
        definition="An existing word",
    )


class TestCreateDictionaryCommand:
    def test_create_dictionary(self, db):
        out = StringIO()
        call_command(
            "create_dictionary",
            "New Dictionary",
            "--prompt=test prompt",
            stdout=out,
        )

        assert Dictionary.objects.filter(name="New Dictionary").exists()
        dictionary = Dictionary.objects.get(name="New Dictionary")
        assert dictionary.slug == "new-dictionary"
        assert "Created dictionary" in out.getvalue()

    def test_create_dictionary_with_slug(self, db):
        out = StringIO()
        call_command(
            "create_dictionary",
            "New Dictionary",
            "--prompt=test prompt",
            "--slug=custom-slug",
            stdout=out,
        )

        dictionary = Dictionary.objects.get(name="New Dictionary")
        assert dictionary.slug == "custom-slug"

    def test_create_dictionary_with_prompt(self, db):
        call_command(
            "create_dictionary",
            "New Dictionary",
            "--prompt=vocabulary words related to cooking",
        )

        dictionary = Dictionary.objects.get(name="New Dictionary")
        assert dictionary.prompt == "vocabulary words related to cooking"

    def test_create_dictionary_duplicate_name(self, dictionary):
        with pytest.raises(CommandError) as exc_info:
            call_command(
                "create_dictionary",
                "Test Dictionary",
                "--prompt=test prompt",
            )

        assert "already exists" in str(exc_info.value)

    def test_create_dictionary_duplicate_slug(self, dictionary):
        with pytest.raises(CommandError) as exc_info:
            call_command(
                "create_dictionary",
                "Different Name",
                "--prompt=test prompt",
                "--slug=test-dictionary",
            )

        assert "slug" in str(exc_info.value)

    def test_strip_strings(self, db):
        out = StringIO()
        call_command(
            "create_dictionary",
            "  New Dictionary  ",
            "--prompt=  test prompt  ",
            "--slug=  custom-slug  ",
            stdout=out,
        )

        dictionary = Dictionary.objects.get(name="New Dictionary")
        assert dictionary.slug == "custom-slug"
        assert dictionary.prompt == "test prompt"


class TestGenerateWordsCommand:
    @pytest.fixture
    def mock_service(self):
        with patch(
            "dailyword.management.commands.generate_words.OpenRouterService"
        ) as mock:
            service_instance = MagicMock()
            mock.return_value = service_instance
            yield service_instance

    def test_generate_words_success(self, dictionary, mock_service):
        mock_service.generate_word_list.return_value = [
            WordDefinition(
                word="Generated1",
                definition="Definition 1",
                example_sentence="Example 1",
                pronunciation="pron1",
                part_of_speech="noun",
            ),
            WordDefinition(
                word="Generated2",
                definition="Definition 2",
                example_sentence="Example 2",
                pronunciation="pron2",
                part_of_speech="verb",
            ),
        ]

        out = StringIO()
        call_command(
            "generate_words",
            "test-dictionary",
            stdout=out,
        )

        assert Word.objects.filter(word="Generated1").exists()
        assert Word.objects.filter(word="Generated2").exists()
        assert "Created: Generated1" in out.getvalue()

    def test_generate_words_by_id(self, dictionary, mock_service):
        mock_service.generate_word_list.return_value = []

        call_command(
            "generate_words",
            str(dictionary.id),
        )

        mock_service.generate_word_list.assert_called_once()

    def test_generate_words_skip_existing(self, dictionary, word, mock_service):
        mock_service.generate_word_list.return_value = [
            WordDefinition(
                word="Existing",  # Same as fixture
                definition="New definition",
                example_sentence="",
                pronunciation="",
                part_of_speech="",
            ),
        ]

        out = StringIO()
        call_command(
            "generate_words",
            "test-dictionary",
            stdout=out,
        )

        assert "Skipped (exists): Existing" in out.getvalue()
        # Original definition should be preserved
        word.refresh_from_db()
        assert word.definition == "An existing word"

    def test_generate_words_dry_run(self, dictionary, mock_service):
        mock_service.generate_word_list.return_value = [
            WordDefinition(
                word="DryRunWord",
                definition="Definition",
                example_sentence="",
                pronunciation="",
                part_of_speech="noun",
            ),
        ]

        out = StringIO()
        call_command(
            "generate_words",
            "test-dictionary",
            "--dry-run",
            stdout=out,
        )

        assert not Word.objects.filter(word="DryRunWord").exists()
        assert "[DRY RUN]" in out.getvalue()
        assert "DryRunWord" in out.getvalue()

    def test_generate_words_with_count(self, dictionary, mock_service):
        mock_service.generate_word_list.return_value = []

        call_command(
            "generate_words",
            "test-dictionary",
            "--count=20",
        )

        mock_service.generate_word_list.assert_called_once_with(
            prompt=dictionary.prompt,
            count=20,
        )

    def test_generate_words_dictionary_not_found(self, db):
        with pytest.raises(CommandError) as exc_info:
            call_command(
                "generate_words",
                "nonexistent",
            )

        assert "not found" in str(exc_info.value)

    def test_generate_words_api_key_missing(self, dictionary):
        with patch(
            "dailyword.management.commands.generate_words.OpenRouterService"
        ) as mock:
            mock.side_effect = OpenRouterError("API key not configured")

            with pytest.raises(CommandError) as exc_info:
                call_command(
                    "generate_words",
                    "test-dictionary",
                )

            assert "API key" in str(exc_info.value)

    def test_generate_words_api_error(self, dictionary, mock_service):
        mock_service.generate_word_list.side_effect = OpenRouterError("API error")

        with pytest.raises(CommandError) as exc_info:
            call_command(
                "generate_words",
                "test-dictionary",
            )

        assert "Failed to generate" in str(exc_info.value)
