# DailyWord

## Setup

### Install Dependencies

Using `uv`:

```bash
uv sync
```

## Running Tests

Run all tests with coverage:

```bash
uv run pytest --cov
```

## Running the Development Server

```bash
uv run django-admin runserver
```

The server will be available at `http://127.0.0.1:8000/`

Admin interface: `http://127.0.0.1:8000/admin/`

## Code Quality Tools

```bash
prek run -va
```
