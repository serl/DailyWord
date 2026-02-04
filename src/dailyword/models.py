import hashlib
from datetime import date

from django.db import models
from django.utils.text import slugify


class Timestamped(models.Model):
    """Abstract base class with created and updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Dictionary(Timestamped):
    """A collection of words organized by theme or language."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta(Timestamped.Meta):
        verbose_name_plural = "dictionaries"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_word_for_date(self, target_date: date) -> Word | None:
        """Get the word assigned to a specific date for this dictionary."""
        words = list(self.words.all().order_by("id"))
        if not words:
            return None

        # Use a deterministic hash based on dictionary id and date
        hash_input = f"{self.id}-{target_date.isoformat()}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        index = hash_value % len(words)
        return words[index]


class Word(Timestamped):
    """A word with its definition and optional image."""

    dictionary = models.ForeignKey(
        Dictionary, on_delete=models.CASCADE, related_name="words"
    )
    word = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    definition = models.TextField()
    example_sentence = models.TextField(blank=True)
    pronunciation = models.CharField(max_length=255, blank=True)
    part_of_speech = models.CharField(max_length=50, blank=True)

    class Meta(Timestamped.Meta):
        ordering = ["word"]
        unique_together = ["dictionary", "slug"]

    def __str__(self) -> str:
        return f"{self.word} ({self.dictionary.name})"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.word)
        super().save(*args, **kwargs)
