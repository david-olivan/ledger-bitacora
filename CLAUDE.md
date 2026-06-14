# CLAUDE.md — Ledger Bitácora

## Project overview

**Ledger Bitácora** (*the inventor's logbook*) is a lightweight, self-hosted project and task management web app with a 1920s inventor's-workbench aesthetic (cream paper, typewriter type, brass/copper fittings). Single-user, container-based, deployed via Dokploy on a home lab.

**Hierarchy:** Project → Bucket → Task  
**Stack:** Django 5.2 + PostgreSQL + HTMX + SortableJS + hand-rolled CSS  
**Language:** Spanish (Spain) — `es-es`

## Development setup

### Docker (recommended)
```bash
cp .env.example .env          # fill in values
docker compose up --build
docker compose exec web python manage.py createsuperuser
```

The `docker-compose.override.yml` mounts source and runs `runserver` for hot-reload.

### Local venv
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in values
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Common management commands
```bash
python manage.py makemigrations workbench   # after changing models
python manage.py migrate
python manage.py makemessages -l es         # after adding new translatable strings
python manage.py compilemessages
python manage.py test                        # run tests
```

## Project structure

```
config/                  Django project: settings, root URLs, WSGI
workbench/               Main app
  models.py              All data models (Project, Bucket, Task, etc.)
  admin.py               Admin registration for all models
  views.py               View functions (all login-required)
  urls.py                App URL patterns
  templates/workbench/   App-specific templates
  static/workbench/      App-specific CSS / JS
templates/               Project-level templates (base.html, registration/)
static/                  Project-level static files (main.css, fonts)
locale/es/LC_MESSAGES/   Spanish translation catalog (django.po / django.mo)
Dockerfile               Web container — python:3.12-slim + Gunicorn
docker-compose.yml       Production: web + db services
docker-compose.override.yml  Dev overrides: source mount + runserver
entrypoint.sh            Container start: migrate → gunicorn
```

## Build order (from PRD §12)

1. [x] Django scaffold + Postgres connection
2. [x] Docker: Dockerfile + docker-compose.yml
3. [x] Models + migrations
4. [x] Auth: login screen, login-required on all views, admin model registration
5. [x] Projects grid view: cards with brass gauges, create / pin / delete
6. [x] Project detail shell + view-switcher toggle (Buckets ↔ Calendar)
7. [x] Buckets view: columns, task cards, task editor (field order below), completion section
8. [x] SortableJS drag-drop between/within buckets + HTMX position persist
9. [x] Tag management: 8 metallic colors, project-scoped, rename propagates everywhere
10. [x] Calendar/Gantt view: month (day columns) and year (week columns) grid
11. [x] Aesthetic pass: cream/paper, typewriter fonts, metallic accents, hand-drawn feel
12. [x] i18n: all strings wrapped, compilemessages wired into Docker build
13. [x] Deployment polish: WhiteNoise, env docs, superuser step, Dokploy notes

## Business rules (enforced in view/form layer)

| Rule | Limit |
|---|---|
| Buckets per project | max 7 |
| Pinned projects | max 5 |
| Tags per task | max 3 |
| Tags per color per project | max 1 (unique together) |
| Bucket order | creation order only — not user-reorderable |

- New projects are **always seeded with a "In Progress" bucket**.
- Completing a task moves it to a **collapsed section at the bottom of its own bucket** (not a global completed pile). Uncompleting returns it to the active list.
- Tags are **project-scoped and shared**: renaming a tag updates it everywhere in the project because tasks reference the shared `Tag` object via `TaskTag`.

## Task editor field order (strict)
1. Title
2. Description / notes
3. Checklist (add / check / remove items — no dates on items)
4. Timing: start date, then end date
5. Tags (pick up to 3 from the project's metallic palette)
6. Mark complete / delete task

## Data model quick reference

```
Project  →  Bucket (max 7)  →  Task  →  ChecklistItem
                                ↕
                            TaskTag  →  Tag (project-scoped, 8 colors)
```

### Tag color enum
`gold`, `silver`, `copper`, `brass`, `bronze`, `gunmetal`, `rose_gold`, `pewter`

## Aesthetic direction

**1920s inventor's workbench / light steampunk-solarpunk.** CSS is hand-rolled — no framework.

| Element | Direction |
|---|---|
| Background | Warm cream `#F5F0E8` with subtle paper grain texture |
| Headings | Typewriter / slab-serif (e.g. Special Elite, Courier Prime) |
| Body | Clean serif or mono (Georgia or Courier Prime) |
| Accents | Brass / copper / gunmetal gradients on controls, gauges, tag chips |
| Gauges | Three small brass instrument gauges per project card (SVG or CSS) |
| Cards | Slight border irregularity for hand-drawn feel |
| Completed | Hand-crossed-out look: irregular strike-through + slight rotation |
| Chrome | Restrained — texture carries the theme, not decorative clutter |

### Metallic CSS custom properties (defined in `static/css/main.css`)
```css
--color-gold:      linear-gradient(135deg, #D4AF37, #F5C842, #B8960C);
--color-silver:    linear-gradient(135deg, #C0C0C0, #E8E8E8, #A8A8A8);
--color-copper:    linear-gradient(135deg, #B87333, #D4905A, #8B5A1E);
--color-brass:     linear-gradient(135deg, #B5A642, #D4C35A, #8B7D1E);
--color-bronze:    linear-gradient(135deg, #CD7F32, #E09050, #9B5E1A);
--color-gunmetal:  linear-gradient(135deg, #2A3439, #404E55, #1A252A);
--color-rose_gold: linear-gradient(135deg, #B76E79, #D4909A, #8B4E5A);
--color-pewter:    linear-gradient(135deg, #8A9BA8, #A8B8C5, #6A7B88);
```

## i18n rules (non-negotiable)

Every user-facing string must be wrapped — even in v1 which ships only Spanish. Nothing hardcoded.

- **Python/views:** `from django.utils.translation import gettext_lazy as _` → `_('My string')`
- **Templates:** `{% load i18n %}` then `{% trans "My string" %}` or `{% blocktrans %}...{% endblocktrans %}`
- **Settings:** `USE_I18N = True`, `LANGUAGE_CODE = 'es-es'`, `LocaleMiddleware` in MIDDLEWARE
- Workflow: `makemessages -l es` → edit `locale/es/LC_MESSAGES/django.po` → `compilemessages`

## Code style

- **No comments** unless the WHY is non-obvious.
- **No type annotations** — keep it readable Django-style Python.
- **Templates:** Django templates only. HTMX for interactivity, not JS-heavy solutions.
- **CSS:** Custom properties for all colors and spacing. BEM-ish class names. No utility framework.
- **JS:** Vanilla JS + SortableJS only. No React, Vue, Alpine, etc.
- Functions should be short and explicit. Prefer clarity over cleverness.

## Environment variables

See `.env.example` for the full list. Required in production:

| Variable | Notes |
|---|---|
| `SECRET_KEY` | Long random string, never committed |
| `DATABASE_URL` | `postgres://user:pass@db:5432/dbname` |
| `ALLOWED_HOSTS` | Comma-separated domain list |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated HTTPS origins (required behind Dokploy proxy) |
| `DEBUG` | Always `false` in production |

## Non-goals (v1)

Do **not** implement: self-registration, multi-user collaboration, project-level tags, bucket reordering, task dependencies, recurring tasks, reminders, mobile-first design, global cross-project calendar, portfolio/program views.
