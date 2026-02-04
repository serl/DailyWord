from datetime import date

import pytest
from django.db import IntegrityError

from dailyword.models import Dictionary, Word


@pytest.fixture
def dictionary(db):
    """Create a test dictionary."""
    return Dictionary.objects.create(
        name="Test Dictionary",
        prompt="vocabulary words for testing",
    )


@pytest.fixture
def word(dictionary):
    """Create a test word."""
    return Word.objects.create(
        dictionary=dictionary,
        word="Example",
        definition="A thing characteristic of its kind",
        example_sentence="This is an example sentence.",
        pronunciation="/igzaempel/",
        part_of_speech="noun",
    )


class TestDictionary:
    def test_str(self, dictionary):
        assert str(dictionary) == "Test Dictionary"

    def test_auto_slug_generation(self, db):
        dictionary = Dictionary.objects.create(
            name="My Test Dictionary",
            prompt="test prompt",
        )
        assert dictionary.slug == "my-test-dictionary"

    def test_manual_slug(self, db):
        dictionary = Dictionary.objects.create(
            name="Test Dictionary",
            slug="custom-slug",
            prompt="test prompt",
        )
        assert dictionary.slug == "custom-slug"

    def test_ordering(self, db):
        Dictionary.objects.create(name="Zebra", prompt="test")
        Dictionary.objects.create(name="Apple", prompt="test")
        Dictionary.objects.create(name="Mango", prompt="test")

        names = list(Dictionary.objects.values_list("name", flat=True))
        assert names == ["Apple", "Mango", "Zebra"]

    def test_get_word_for_date_empty_dictionary(self, dictionary):
        result = dictionary.get_word_for_date(date(2024, 1, 1))
        assert result is None

    def test_get_word_for_date_single_word(self, dictionary, word):
        result = dictionary.get_word_for_date(date(2024, 1, 1))
        assert result == word

    def test_get_word_for_date_deterministic(self, dictionary):
        # Create multiple words
        for i in range(10):
            Word.objects.create(
                dictionary=dictionary,
                word=f"Word{i}",
                definition=f"Definition {i}",
            )

        # Same date should always return same word
        date1 = date(2024, 6, 15)
        result1 = dictionary.get_word_for_date(date1)
        result2 = dictionary.get_word_for_date(date1)
        assert result1 == result2

        # Different dates may return different words (but consistently)
        date2 = date(2024, 6, 16)
        result3 = dictionary.get_word_for_date(date2)
        result4 = dictionary.get_word_for_date(date2)
        assert result3 == result4

    def test_get_word_for_date_different_dictionaries(self, db):
        dict1 = Dictionary.objects.create(name="Dictionary 1", prompt="test")
        dict2 = Dictionary.objects.create(name="Dictionary 2", prompt="test")

        # Same words in both
        for i in range(5):
            Word.objects.create(
                dictionary=dict1,
                word=f"Word{i}",
                definition=f"Definition {i}",
            )
            Word.objects.create(
                dictionary=dict2,
                word=f"Word{i}",
                definition=f"Definition {i}",
            )

        test_date = date(2024, 1, 1)
        # Different dictionaries should potentially return different words
        # due to different dictionary IDs in the hash
        result1 = dict1.get_word_for_date(test_date)
        result2 = dict2.get_word_for_date(test_date)
        # Both should be valid words
        assert result1 is not None
        assert result2 is not None


class TestWord:
    def test_str(self, word):
        assert str(word) == "Example (Test Dictionary)"

    def test_ordering(self, dictionary):
        Word.objects.create(dictionary=dictionary, word="Zebra", definition="Z")
        Word.objects.create(dictionary=dictionary, word="Apple", definition="A")
        Word.objects.create(dictionary=dictionary, word="Mango", definition="M")

        words = list(dictionary.words.values_list("word", flat=True))
        assert words == ["Apple", "Mango", "Zebra"]

    def test_unique_together_word_dictionary(self, dictionary):
        Word.objects.create(
            dictionary=dictionary,
            word="Test",
            definition="First",
        )

        with pytest.raises(IntegrityError):
            Word.objects.create(
                dictionary=dictionary,
                word="Test",  # Same word in same dictionary
                definition="Second",
            )

    def test_same_word_different_dictionaries(self, db):
        dict1 = Dictionary.objects.create(name="Dictionary 1", prompt="test")
        dict2 = Dictionary.objects.create(name="Dictionary 2", prompt="test")

        # Same word in different dictionaries should work
        Word.objects.create(
            dictionary=dict1,
            word="Test",
            definition="First",
        )
        word2 = Word.objects.create(
            dictionary=dict2,
            word="Test",
            definition="Second",
        )
        assert word2.word == "Test"

    def test_optional_fields(self, dictionary):
        word = Word.objects.create(
            dictionary=dictionary,
            word="Minimal",
            definition="Just the essentials",
        )
        assert word.example_sentence == ""
        assert word.pronunciation == ""
        assert word.part_of_speech == ""
