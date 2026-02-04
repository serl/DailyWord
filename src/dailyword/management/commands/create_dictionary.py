from typing import Annotated

import typer
from django.core.management.base import CommandError
from django_typer.management import TyperCommand

from dailyword.models import Dictionary


class Command(TyperCommand):
    help = "Create a new dictionary"

    def handle(
        self,
        name: Annotated[str, typer.Argument(help="Name of the dictionary")],
        prompt: Annotated[str, typer.Option(help="Prompt used for AI word generation")],
        slug: Annotated[
            str,
            typer.Option(help="URL-friendly slug (auto-generated if not provided)"),
        ] = "",
    ):
        # Check if dictionary with same name exists
        if Dictionary.objects.filter(name=name).exists():
            raise CommandError(f"Dictionary '{name}' already exists.")

        # Check if slug exists (if provided)
        if slug and Dictionary.objects.filter(slug=slug).exists():
            raise CommandError(f"Dictionary with slug '{slug}' already exists.")

        dictionary = Dictionary.objects.create(
            name=name.strip(),
            slug=slug.strip(),
            prompt=prompt.strip(),
        )

        self.secho(
            f"Created dictionary: {dictionary.name} (slug: {dictionary.slug})",
            fg=typer.colors.GREEN,
        )
