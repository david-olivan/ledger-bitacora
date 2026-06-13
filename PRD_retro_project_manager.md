# PRD — Retro Project & Task Manager ("The Workbench")

## 1. Summary

A lightweight, self-hosted project and task management web app with a 1920s
inventor's-workbench aesthetic (cream paper, typewriter type, brass/copper
fittings, hand-drawn marks). Built to be shown on camera as the creator's own
alternative to Planner / Trello / GitHub Projects. Single-user, container-based,
deployed via Dokploy in a home lab.

The hierarchy is **Project → Bucket → Task**. Tasks carry a title, notes, a
checklist, dates, tags, and a completion state. The app offers a **buckets
(board) view** and a **calendar/Gantt view** per project, plus a **projects
grid** entry view with brass-gauge metrics.

## 2. Goals & non-goals

### Goals
- A streamlined, minimalistic, visually distinctive PM tool that looks great on video.
- Drag-and-drop task management between and within buckets.
- A per-project Gantt rendered as a colored-box grid driven purely by task dates.
- Lightweight stack, fully containerized, easy to deploy via Dokploy.

### Non-goals (explicitly out of scope for v1)
- Portfolios / programs and **project-level** tagging (tags here apply to tasks, not projects).
- Self-registration. Users are created via the Django admin.
- Multi-user collaboration, sharing, permissions beyond a single owner.
- Task dependencies, recurring tasks, reminders, notifications.
- Reordering of buckets.
- Mobile-first design (should be usable but desktop is the target for filming).

## 3. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | **Django** (latest LTS) | Built-in auth, admin, ORM, migrations. |
| Database | **PostgreSQL** | Separate container. |
| Templating | Django templates | Server-rendered. |
| Interactivity | **HTMX** | View switching, inline edits, partial updates. |
| Drag & drop | **SortableJS** | Between buckets and within a bucket. |
| Styling | Hand-rolled CSS (no heavy framework) | Keeps the bespoke retro look and the bundle light. |
| Server | Gunicorn | Behind Dokploy's reverse proxy. |
| Static files | WhiteNoise | Avoids a separate static server. |
| i18n | Django's built-in `gettext` / `django.po` | UI ships in Spanish (Spain); structured for more languages later. |

### Containers
- **web**: Django + Gunicorn (one image).
- **db**: PostgreSQL (official image, named volume for persistence).
- `docker-compose.yml` wiring the two, with environment variables for secrets
  and DB connection. Compose is Dokploy-compatible.

Recommended Django libraries to evaluate during build: `django-environ`
(env config), `whitenoise` (static), `psycopg[binary]` (Postgres driver).
Avoid pulling in anything not strictly needed.

## 4. Data model

### User
Django's built-in `User`. Single owner in practice; all entities are scoped to
the owning user (foreign key) so the model stays multi-user-ready without
building multi-user UX.

### Project
- `id`
- `name` (string, required)
- `owner` (FK → User)
- `created_at`, `updated_at`
- `pinned` (bool) — whether it appears in the top-anchored projects list
- `pin_order` (int, nullable) — order among pinned projects (max 5 pinned)

On creation, a project is seeded with one default bucket named **"In Progress"**
(the default inbox / priority bucket).

### Bucket
- `id`
- `project` (FK → Project, cascade delete)
- `name` (string, required, renameable)
- `order` (int) — fixed creation order; **not** user-reorderable
- Constraint: **max 7 buckets per project** (enforced in the form / view layer).

### Task
- `id`
- `bucket` (FK → Bucket, cascade delete)
- `title` (string, required)
- `notes` (text, optional)
- `start_date` (date, optional)
- `end_date` (date, optional)
- `completed` (bool, default false)
- `completed_at` (datetime, nullable)
- `position` (int) — manual order within its bucket (drives drag ordering)
- `created_at`, `updated_at`

Field order in the task editor UI: **Title → Description/Notes → Checklist →
Timing (start then end).**

### ChecklistItem
- `id`
- `task` (FK → Task, cascade delete)
- `text` (string)
- `checked` (bool, default false)
- `position` (int)

(Checklist items have no dates — text + checked only.)

### Tag (project-scoped, reusable)
- `id`
- `project` (FK → Project, cascade delete) — a tag belongs to a project, not a task
- `name` (string)
- `color` (enum, one of the 8 metallic colors)
- Constraint: **one tag per color per project** (unique together on
  `project` + `color`). A project therefore has at most 8 tags, one of each
  metallic color.

> Design note: tags are **shared across the project**. When you assign a color
> to a task you pick from the project's existing tags (or create that color's
> tag if it doesn't exist yet) and give it a name. Renaming a tag — e.g.
> changing the name of the *gold* tag — updates it **everywhere that tag is used
> in the project**, because tasks reference the shared Tag, not a per-task copy.

### TaskTag (join)
- `id`
- `task` (FK → Task, cascade delete)
- `tag` (FK → Tag, cascade delete)
- Constraint: **max 3 tags per task** (enforced in the form / view layer);
  unique together on `task` + `tag` so the same tag can't be applied twice.

> Implemented as an explicit many-to-many (`Task` ↔ `Tag` through `TaskTag`).
> Assigning a tag to a task creates a join row; renaming the underlying Tag is
> reflected on every task that links to it.

### Metallic color palette (fixed, 8 options)
`gold`, `silver`, `copper`, `brass`, `bronze`, `gunmetal`, `rose_gold`, `pewter`.
Each maps to a CSS variable with an appropriate metallic gradient/sheen.

## 5. Navigation & layout

### Sidebar (persistent, left)
- **Top**: app logo + name.
- **Projects** link → opens the Projects grid view.
- **Pinned projects**: up to **5** top-anchored project shortcuts.
- **Bottom**: account section + **Log out**.

### Projects grid view (home)
- A grid of project cards.
- Each card shows:
  - Project **name**.
  - **Three brass gauges**: total tasks, remaining (incomplete) tasks, completed tasks.
  - (No project tags / portfolio in v1.)
- Action to create a new project.
- Affordance to pin/unpin a project (respecting the 5-pin limit) and to delete a
  project (cascades to buckets, tasks, checklist items, tags — confirmed
  acceptable).

### Project detail view
A view-switcher control at the **top-right**: a dial/toggle between:
1. **Buckets** (board) view.
2. **Calendar / Gantt** view.

## 6. Buckets (board) view

- Horizontal columns, one per bucket, in fixed creation order.
- Default bucket **"In Progress"** present on every new project; up to 7 buckets total.
- Buckets are **renameable**, **not reorderable**.
- Add-bucket control (disabled once 7 exist).
- Tasks render as cards within a bucket:
  - Title, up to 3 metallic tag chips, a checklist progress hint, and date range if set.
- **Drag & drop (SortableJS)**:
  - Move a task **between** buckets.
  - Reorder tasks **within** a bucket (manual ordering only; no sort options).
  - Position changes persist via an HTMX call updating `bucket` and `position`.
- **Completion**: marking a task complete removes it from the active list and
  drops it into a **collapsed "completed" section at the bottom of its own
  bucket** (per-bucket, not a global pile). The section can expand/collapse.
  Uncompleting returns the task to the active list.

### Task editor
Opened from a card (modal or slide-over). Fields in order:
1. Title
2. Description / notes
3. Checklist (add / check / remove items)
4. Timing: start date, then end date
5. Tags (pick up to 3 of the project's metallic tags; set a tag's name/color here)
6. Mark complete / delete task

## 7. Calendar / Gantt view (per project)

A spreadsheet-like grid: tasks listed down the left (vertical axis), time across
the top (horizontal axis), with colored boxes spanning each task's
`start_date`–`end_date`. No dependencies, no arrows — just filled bars.

- **Month view (default)**: columns = **days** of the month; horizontal scroll
  if needed.
- **Year view**: a button toggles to columns = **weeks**, boxes drawn per week.
- Buttons to switch between month and year granularity.
- Tasks without dates are listed but draw no bar (or are visually muted).
- Bar color can reuse the task's primary tag color (or a default brass) to stay on-theme.
- Scope: **project-level only** (no global cross-project calendar in v1).

## 8. Authentication

- **Minimalistic login screen** only. No registration.
- Admin credentials seeded into the database; Django admin used to create/manage users.
- Standard Django session auth; all project/task views require login and are
  scoped to the logged-in user.
- Log out from the sidebar.

## 9. Aesthetic direction

1920s inventor's workbench / light steampunk-solarpunk:
- **Paper**: warm cream background with subtle paper grain/texture.
- **Type**: typewriter / slab-serif display face for headings; a clean readable
  serif or mono for body.
- **Metals**: brass, copper, gunmetal accents on controls, gauges, the
  view-switch dial, and tag chips (with sheen/gradient).
- **Hand-drawn feel (optional but desired)**: task cards and checklist
  checkboxes styled to look hand-drawn; completed checklist items / tasks given
  a hand-crossed-out look (e.g. an irregular strike-through, slight rotation).
- **Gauges**: three small brass instrument gauges on each project card (total /
  remaining / completed).
- Restrained, minimal chrome — the texture and metal accents carry the theme, not clutter.

## 10. Internationalization (i18n)

- **Default and only shipping language for v1: Spanish (Spain), `es-ES`.** All
  user-facing interface copy is written in `es-ES`.
- Built on **Django's standard i18n framework** so additional languages can be
  added later without rework:
  - `USE_I18N = True`; `LANGUAGE_CODE = 'es-es'`.
  - `LANGUAGES` setting lists supported locales (starts with just `es`).
  - `LocaleMiddleware` enabled.
  - A `locale/` directory holds `.po`/`.mo` translation catalogs per language.
- **All interface strings wrapped for translation from the start**: `gettext` /
  `gettext_lazy` in Python, `{% trans %}` / `{% blocktrans %}` in templates.
  Even though only Spanish ships now, nothing should be hardcoded as a bare
  literal — this is what makes adding a language a translation task, not a
  refactor.
- Source message catalog generated with `makemessages` and compiled with
  `compilemessages` (compilation wired into the build/entrypoint).
- Dates, numbers, and the calendar/Gantt respect locale formatting
  (`USE_L10N` behavior, Spain conventions: day-first dates, week starting Monday).
- Future-language workflow (documented): add the locale to `LANGUAGES`, run
  `makemessages -l <code>`, translate the `.po`, `compilemessages`. A language
  switcher UI is **out of scope for v1** but the framework leaves room for it.


## 11. Packaging & deployment

### Container topology
Two services, defined together in `docker-compose.yml`:

- **web** — the Django app served by Gunicorn (one image, built from the repo Dockerfile).
- **db** — PostgreSQL from the official image, with a named volume for persistence.

The web service depends on db and waits for it to be healthy before starting.

### Dockerfile (web) requirements
- Base on an official slim Python image (e.g. `python:3.12-slim`).
- Install build/runtime deps needed for `psycopg` and Postgres client libs.
- Create a non-root app user and run as that user.
- Copy dependency manifest first and install (cache-friendly layer), then copy app code.
- Collect static files at build time (`collectstatic --noinput`) so WhiteNoise can serve them.
- Expose the Gunicorn port (e.g. 8000).
- Entrypoint script that, on container start:
  1. waits for the database,
  2. runs `migrate --noinput`,
  3. launches Gunicorn (e.g. `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3`).
- Superuser creation is a documented one-time manual step (or an optional,
  idempotent env-gated bootstrap), not run on every start.

### docker-compose.yml requirements
- `web` service:
  - built from the local Dockerfile,
  - reads config from environment (`.env` file / Dokploy env), never hardcoded secrets,
  - depends on `db` (with healthcheck condition),
  - publishes the app port for Dokploy's reverse proxy to bind.
- `db` service:
  - official `postgres` image (pinned major version),
  - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` from env,
  - named volume mounted at the Postgres data dir,
  - a healthcheck using `pg_isready`.
- A named volume for Postgres data (survives redeploys).
- No source bind-mounts in the production compose (image is self-contained);
  an optional override file may add mounts for local dev.

### Environment / configuration
All via environment variables (12-factor), supplied through a `.env` file
locally and Dokploy's env settings in production:
- `SECRET_KEY`
- `DEBUG` (false in production)
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS` (the deployed domain, for HTTPS behind the proxy)
- `DATABASE_URL` (or discrete `POSTGRES_*` + host/port) parsed via `django-environ`
- `DJANGO_SUPERUSER_*` (optional, only for the bootstrap path)

### Static files
- WhiteNoise serves static assets from the web container (no separate static service).
- `collectstatic` handled at build; compressed/manifest storage enabled.

### Dokploy / home-lab notes
- Target host: Ubuntu, Docker installed, Dokploy managing the app.
- Dokploy builds from the compose file and provides the reverse proxy + TLS.
- Persistent Postgres volume must be preserved across deploys.
- The full flow — install Ubuntu → install Dokploy → deploy this compose stack —
  is the intended subject of a video, so the compose + Dockerfile should be
  clean and self-explanatory on screen.

## 12. Suggested build order (for Claude Code)

1. Project scaffold: Django project, app, settings via env, Postgres connection.
2. Docker: Dockerfile for web, `docker-compose.yml` with db + volume, local run.
3. Models + migrations: Project, Bucket (with default-bucket creation + 7-cap),
   Task, ChecklistItem, Tag (project-scoped, one per color), TaskTag join
   (3-tag-per-task cap).
4. Auth: login screen, login-required scoping, admin registration of models.
5. Projects grid view + brass gauges + create/pin/delete.
6. Project detail shell + top-right view switcher.
7. Buckets view: columns, task cards, task editor (correct field order),
   completion → collapsed section.
8. SortableJS drag/drop between and within buckets, persisting position/bucket via HTMX.
9. Tags: project-scoped tag management (8 metallic colors, one tag per color,
   renaming propagates project-wide); task tagging UI (assign up to 3 of the
   project's tags).
10. Calendar/Gantt view: month (days) + year (weeks) grid with colored bars.
11. Aesthetic pass: cream/paper, typewriter type, metallic accents, hand-drawn
    cards/checkboxes/strike-through.
12. i18n: enable Django i18n, set `es-ES`, wrap all strings, generate and
    compile the Spanish catalog, wire `compilemessages` into the build.
13. Deployment polish: collectstatic, WhiteNoise, env docs, superuser step,
    Dockerfile + compose, Dokploy notes.

## 13. Open items / future (post-v1)
- Portfolios / programs and project tags.
- Global cross-project calendar.
- Task dependencies on the Gantt.
- Multi-user UX (the data model already carries `owner`).
