# DailyWord

A Django application for learning new words with AI-generated definitions and images.

## Features

- **Dictionaries**: Organize words into themed collections
- **Words**: Store vocabulary with definitions, examples, pronunciation, and images
- **Daily Word API**: Get a different word each day for any dictionary
- **Admin Interface**: Full Django admin for managing all content

## Setup

### System Dependencies

The word image generation uses Cairo for SVG to PNG conversion.

**macOS:**

```bash
brew install cairo
```

**Ubuntu/Debian:**

```bash
apt-get install libcairo2
```

### Install Dependencies

Using `uv`:

```bash
uv sync
```

### Database Setup

Run migrations:

```bash
uv run django-admin migrate
```

Create a superuser for admin access:

```bash
uv run django-admin createsuperuser
```

## Running the Development Server

```bash
uv run django-admin runserver
```

The server will be available at `http://127.0.0.1:8000/`

Admin interface: `http://127.0.0.1:8000/admin/`

## Management Commands

### Create a Dictionary

```bash
uv run django-admin create_dictionary "English Vocabulary" \
  --prompt="intermediate English vocabulary words about cooking and food" \
  --slug=english-vocabulary
```

Options:

- `--prompt`: Prompt used for AI word generation (required)
- `--slug`: Custom URL-friendly slug (auto-generated if not provided)

### Generate Words with AI

Generate vocabulary words for a dictionary using AI:

```bash
uv run django-admin generate_words english-vocabulary --count=20
```

Options:

- `--count`: Number of words to generate (default: 10)
- `--dry-run`: Preview words without saving

## Running Tests

Run all tests with coverage:

```bash
uv run pytest --cov
```

## Code Quality Tools

```bash
prek run -va
```

## Deployment

Use the provided `Dockerfile` to build and deploy the application.

Set the environment variables as in `.env.example`.

Exposed port: `8000`.
