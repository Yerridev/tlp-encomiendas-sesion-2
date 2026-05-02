# AGENTS

## Scope
- Django project rooted at `manage.py`; settings in `config/settings.py` and URLs in `config/urls.py`.
- Apps registered: `clientes`, `envios`, `rutas`; only `envios` is wired into root URLs.

## Environment
- Settings use `python-decouple`; `.env` is loaded by docker-compose `env_file` (see `.env.example`).
- If `DB_ENGINE` is missing, settings fall back to SQLite even when Postgres is running; set `DB_ENGINE=django.db.backends.postgresql` plus `DB_HOST=db`/`DB_PORT=5432` in `.env` to use the Docker DB.
- CSRF trusted origin includes `http://localhost:8080` (matches nginx in docker-compose).

## Run / Docker
- `docker-compose.yml` starts `web` via `entrypoint.sh` (patches Django migrations loader, runs `migrate`, then `runserver 0.0.0.0:8000`).
- `web` is exposed directly on `http://localhost:8000`; nginx is optional (`http://localhost:8080`).
- Postgres runs on `5432`, pgAdmin on `http://localhost:5050`.

## Entry Points
- Root routes: `/admin/` and the `envios` app at `/`.
- `envios/urls.py` defines login/logout and main dashboard/encomiendas flows.
