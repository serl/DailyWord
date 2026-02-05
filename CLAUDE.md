# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DailyWord is a Django application for learning new words with AI-generated definitions and images. It provides themed word dictionaries with a daily word API that uses deterministic hash-based selection (same word shown all day, changes at midnight).

## Tech Stack

- Python 3.14, Django 6.0.2
- Package manager: uv (exact version pinning)
- Database: PostgreSQL (production) / SQLite (development)
- AI integration: OpenRouter API for word generation
- Image processing: Pillow

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
    ├── management/commands/  # CLI commands
    └── services/openrouter.py  # AI word generation
tests/                # Mirrors src/ structure
```

## Architecture

**Models:**

- `Dictionary`: Word collections with name, slug, and AI prompt
- `Word`: Vocabulary items (word, definition, example_sentence, pronunciation, part_of_speech) linked to a dictionary

**Key pattern:** `Dictionary.get_word_for_date()` uses MD5 hash of dictionary ID + date for deterministic daily word selection.

**API:** `/api/daily-word/<dictionary_slug>/<width>x<height>/` returns a generated image of the daily word.

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
