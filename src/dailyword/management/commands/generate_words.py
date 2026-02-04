from typing import Annotated

import typer
from django.core.management.base import CommandError
from django_typer.management import TyperCommand

from dailyword.models import Dictionary, Word
from dailyword.services import OpenRouterService
from dailyword.services.openrouter import OpenRouterError


class Command(TyperCommand):
    help = "Generate words with definitions for a dictionary using AI"

    def handle(
        self,
        dictionary: Annotated[
            str, typer.Argument(help="Dictionary slug or ID to add words to")
        ],
        count: Annotated[int, typer.Option(help="Number of words to generate")] = 10,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run", help="Print words without saving to database"),
        ] = False,
    ):
        dict_obj = self._get_dictionary(dictionary)

        self.secho(f"Generating {count} words for dictionary '{dict_obj.name}'")

        try:
            service = OpenRouterService()
        except OpenRouterError as e:
            raise CommandError(str(e)) from e

        try:
            word_definitions = service.generate_word_list(
                prompt=dict_obj.prompt,
                count=count,
            )
        except OpenRouterError as e:
            raise CommandError(f"Failed to generate words: {e}") from e

        self.secho("\nWords received:", fg=typer.colors.YELLOW)
        for wd in word_definitions:
            self.secho(f"\n  {wd.word} ({wd.part_of_speech})")
            self.secho(f"    Definition: {wd.definition}")
            self.secho(f"    Example: {wd.example_sentence}")

        if dry_run:
            self.secho("\n[DRY RUN] Exiting", fg=typer.colors.YELLOW)
            return

        created_count = 0
        skipped_count = 0

        for wd in word_definitions:
            word, created = Word.objects.get_or_create(
                dictionary=dict_obj,
                word=wd.word,
                defaults={
                    "definition": wd.definition,
                    "example_sentence": wd.example_sentence,
                    "pronunciation": wd.pronunciation,
                    "part_of_speech": wd.part_of_speech,
                },
            )
            if created:
                created_count += 1
                self.secho(f"  Created: {word.word}", fg=typer.colors.GREEN)
            else:
                skipped_count += 1
                self.secho(f"  Skipped (exists): {word.word}", fg=typer.colors.YELLOW)

        self.secho(
            f"\nDone! Created {created_count} words, skipped {skipped_count} existing.",
            fg=typer.colors.GREEN,
        )

    def _get_dictionary(self, identifier: str) -> Dictionary:
        """Get dictionary by slug or ID."""
        try:
            return Dictionary.objects.get(slug=identifier)
        except Dictionary.DoesNotExist:
            pass

        try:
            return Dictionary.objects.get(pk=int(identifier))
        except (Dictionary.DoesNotExist, ValueError):
            pass

        raise CommandError(
            f"Dictionary '{identifier}' not found. "
            "Use the slug or ID of an existing dictionary."
        )
