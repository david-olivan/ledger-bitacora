<p align="center">
  <img src="static/img/logo.svg" alt="The Workbench" width="380">
</p>

<p align="center">
  <em>Gestor de proyectos retro — el banco de trabajo del inventor.</em><br>
  A lightweight, self-hosted project &amp; task manager with a 1920s inventor's-workbench aesthetic.
</p>

<p align="center">
  <img alt="Django 5.2" src="https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white">
  <img alt="Python 3.12" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="PostgreSQL 16" src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white">
  <img alt="HTMX" src="https://img.shields.io/badge/HTMX-1.9-3366CC">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-B5A642">
</p>

---

## Overview

**The Workbench** is a single-user, container-based project manager built as a
bespoke alternative to Planner / Trello / GitHub Projects. The hierarchy is
**Project → Bucket → Task**, with a drag-and-drop board view and a per-project
calendar/Gantt view, all wrapped in a warm cream-paper, brass-and-copper
aesthetic. The UI ships in **Spanish (Spain)** and is fully internationalized.

> Cream paper, typewriter type, brass instrument gauges — built to look as good
> on camera as it is to use.

## Features

- **Projects grid** — cards with three brass instrument gauges, pin (max 5) and delete.
- **Buckets board** — up to 7 fixed-order columns per project, always seeded with an *In Progress* bucket.
- **Task editor** — title, notes, checklist, start/end dates, up to 3 metallic tags, complete/delete.
- **Drag &amp; drop** — reorder tasks within and between buckets (SortableJS), persisted over HTMX.
- **Completion** — completed tasks collapse into a per-bucket section, not a global pile.
- **Project-scoped tags** — 8 metallic colors, one per color per project; renaming propagates everywhere.
- **Calendar / Gantt** — month grid with colored bars driven purely by task dates.
- **i18n-first** — every string wrapped for translation; Spanish catalog compiled into the image.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Django 5.2 (auth, admin, ORM, migrations) |
| Database | PostgreSQL 16 |
| Interactivity | HTMX + SortableJS (no SPA framework) |
| Styling | Hand-rolled CSS, custom properties, BEM-ish — no framework |
| Server | Gunicorn behind a reverse proxy |
| Static files | WhiteNoise (compressed manifest storage) |
| Config | `django-environ` (12-factor env vars) |
| Deployment | Docker Compose, Dokploy on a home lab |

## Quick start

### Docker (recommended)

```bash
cp .env.example .env          # fill in SECRET_KEY, DB creds, hosts
docker compose up --build
docker compose exec web python manage.py createsuperuser
```

The app is served at `http://localhost:8000`. `docker-compose.override.yml`
mounts the source and runs `runserver` for hot-reload during development.

### Local virtualenv

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # point DATABASE_URL at your Postgres (or sqlite for a quick spin)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Users are created via the Django admin (`/admin/`) — there is no self-registration.

## Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Notes |
|---|---|
| `SECRET_KEY` | Long random string, never committed |
| `DATABASE_URL` | `postgres://user:pass@db:5432/dbname` |
| `ALLOWED_HOSTS` | Comma-separated domain list |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated HTTPS origins (required behind a TLS proxy) |
| `DEBUG` | Always `false` in production |

## Project structure

```
config/                  Django project: settings, root URLs, WSGI
workbench/               Main app: models, views, forms, admin, urls
  templates/workbench/   App templates (board, calendar, task editor, partials)
templates/               base.html + registration/login
static/
  css/main.css           Hand-rolled stylesheet (theme custom properties)
  img/                   Logo + app icon (SVG)
locale/es/LC_MESSAGES/   Spanish translation catalog
Dockerfile               Web image — python:3.12-slim + Gunicorn
docker-compose.yml       Production: web + db
docker-compose.override.yml  Dev overrides: source mount + runserver
entrypoint.sh            Container start: migrate → gunicorn
```

## Common management commands

```bash
python manage.py makemigrations workbench   # after changing models
python manage.py migrate
python manage.py makemessages -l es         # after adding translatable strings
python manage.py compilemessages
python manage.py test                        # run tests
```

## Deployment

Two services in `docker-compose.yml`: **web** (Django + Gunicorn, built from the
Dockerfile) and **db** (PostgreSQL with a named volume). The web container
collects static files and compiles messages at build time, then on start waits
for the database, runs migrations, and launches Gunicorn. Dokploy builds from
the compose file and provides the reverse proxy and TLS; the Postgres volume is
preserved across deploys.

## Aesthetic

1920s inventor's workbench / light steampunk-solarpunk: warm cream `#F5F0E8`
paper, typewriter/slab-serif headings (Special Elite, Courier Prime), and
brass/copper/gunmetal metallic gradients on gauges, controls, and tag chips. The
app icon is a small brass instrument gauge — the same motif used on the project
cards.

## License

[MIT](LICENSE) © David Oliván Malagón
