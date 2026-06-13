FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings

RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system app && adduser --system --group app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build-time dummy values; real secrets are injected at runtime via env
RUN SECRET_KEY=build-only DATABASE_URL=sqlite:////tmp/build.db \
    python manage.py collectstatic --noinput

RUN python manage.py compilemessages

RUN chown -R app:app /app

RUN chmod +x /app/entrypoint.sh

USER app

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
