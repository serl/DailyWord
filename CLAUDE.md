# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DailyWord is a Django application for learning new words with AI-generated definitions and images. It provides themed word dictionaries with a daily word API that uses deterministic hash-based selection (same word shown all day, changes at midnight).

## Tech Stack

- Python 3.14, Django 6.0.2
- Package manager: uv (exact version pinning)
- Database: PostgreSQL (production) / SQLite (development)
- AI integration: OpenRouter API for word generation
- Image rendering: Pillow (ImageDraw, no system dependencies)
- Snapshot testing: syrupy

## Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run django-admin runserver

# Database migrations
uv run django-admin migrate

# Run tests with coverage
uv run pytest --cov

# Run single test file
uv run pytest tests/test_dailyword/test_models.py

# Run single test
uv run pytest tests/test_dailyword/test_models.py::test_function_name -v

# Update snapshot tests after rendering changes
uv run pytest --snapshot-update

# Code quality (runs all pre-commit hooks)
prek run -a
```

## Project Structure

```text
src/
├── config/           # Django settings, root URLs, WSGI
└── dailyword/        # Main app
    ├── models.py     # Dictionary, Word models
    ├── admin.py      # Django admin configuration
    ├── views.py      # API views (DailyWordImageView)
    ├── rendering.py  # Pillow-based image generation
    ├── fonts/        # Bundled DejaVu Sans TTF fonts
    ├── management/commands/  # CLI commands
    └── services/openrouter.py  # AI word generation
tests/                # Mirrors src/ structure
```

## Architecture

**Models:**

- `Dictionary`: Word collections with name, slug, and AI prompt
- `Word`: Vocabulary items (word, definition, example_sentence, pronunciation, part_of_speech) linked to a dictionary

**Key pattern:** `Dictionary.get_word_for_date()` uses MD5 hash of dictionary ID + date for deterministic daily word selection.

**Rendering:** `rendering.py` draws word images directly with Pillow's `ImageDraw` in grayscale mode `"L"`. Bundled DejaVu Sans fonts ensure deterministic rendering across platforms. The image includes today's word and optionally yesterday's word as a reminder section.

**API:** `/api/daily-word/<dictionary_slug>/<width>x<height>/` returns a generated image of the daily word (with yesterday's word shown below a divider).

## Management Commands

```bash
# Create a dictionary (prompt is used for AI word generation)
uv run django-admin create_dictionary "Name" --prompt="Generate intermediate cooking vocabulary"

# Generate words with AI (requires OPENROUTER_API_KEY)
uv run django-admin generate_words <slug> --count=10 --dry-run
```

## Environment Variables

Required for production: `SECRET_KEY`, `BASE_URL`, `DATABASE_URL`, `OPENROUTER_API_KEY`

See `.env.example` for all options.

## Development policies

We try to have 100% test coverage when that makes sense.
When working on new features, start by writing tests that define the expected behavior, then implement the code to make those tests pass.

## CLAUDE.md maintenance

This file should be kept up to date automatically. When working on the project, update CLAUDE.md with any new discoveries: architecture patterns, conventions, commands, gotchas, or other useful context.
