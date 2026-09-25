# OcéENS

OcéENS is the EPF platform for course feedback. Teaching teams create surveys, students answer them, and authorized staff review, export, and summarize the responses.

The application is built with FastAPI, SQLModel/SQLite, Jinja templates, and a small amount of browser-side JavaScript. Its user interface is in French. In project documentation, *sondage* and *synthèse* are retained as product terms; see [CONTEXT.md](CONTEXT.md).

## First run

Requirements: [uv](https://docs.astral.sh/uv/) and Docker Compose if you want to use the container. The Python version is declared in `.python-version` and supported versions are constrained in `pyproject.toml`.

Clone the `course-2026` branch, then create the local configuration file from the supplied template:

```bash
git clone --branch course-2026 https://github.com/EPF-MDE/OceENS.git
cd OceENS
cp .env.example .env
uv sync --frozen
```

On Windows PowerShell, use `Copy-Item .env.example .env` instead of `cp`. Run `uv sync --frozen` from the repository root to install the exact locked dependencies and the application package.

The example configuration selects development authentication. It requires no Microsoft Entra credentials, and the application can start without an LLM key; in that case, LLM-generated *synthèses* are unavailable. Development authentication allows signing in as users in the local database and must never be exposed as a production service. See the configuration table below before changing any values.

### Run locally

```bash
uv run uvicorn oceens.main:app --reload --port 8000
```

The same command works in Windows PowerShell. `uv` creates and manages the project environment using the declared Python version and lockfile.

Open <http://localhost:8000>. The application initializes its SQLite database and demonstration data on startup. Stop it with Ctrl+C.

### Run with Docker Compose

The `.env` copy above is required because Compose loads that file. From the repository root, run:

```bash
docker compose up --build
```

Open <http://localhost:8000>. Stop the application with Ctrl+C, then remove the containers with `docker compose down`. The database is persisted in the configured host directory.

## Configuration

`.env.example` is the reference for application and Compose configuration. Copy it to `.env`; keep local credentials out of Git. Each variable read by the application is listed here once.

| Variable | Purpose and behavior |
| --- | --- |
| `AUTH_MODE` | Authentication mode: `dev` or `entra`; defaults to `entra` if unset. The example selects `dev` for a credential-free local first run. Never use `dev` in production. |
| `DEV_LOGIN_KEY` | Optional shared key for the development login page. Empty means development login is open; ignored in Entra mode. |
| `ALLOWED_DOMAINS` | Comma-separated email domains allowed to sign in. The development default is `epf.fr,epfedu.fr`. |
| `SECRET_KEY` | Session-cookie signing key. Required in Entra mode. In development, an empty value generates an ephemeral key and sessions do not survive a restart. Generate a private value with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. |
| `ENTRA_CLIENT_ID` | Microsoft Entra application/client ID; required in Entra mode. |
| `ENTRA_CLIENT_SECRET` | Microsoft Entra client secret; required in Entra mode. |
| `ENTRA_TENANT_ID` | Microsoft Entra tenant ID; required in Entra mode. |
| `REDIRECT_URI` | Entra sign-in callback URI. The application has a fallback, but a deployed Entra application must use its registered callback URL. |
| `LOCAL_DATABASE_DIR` | SQLite database directory. Defaults to `database/` in the repository; Compose uses it as the host directory mounted for database persistence. |
| `LLM_API_KEY` | API key for the default EPF Ollama provider. Empty is valid for startup, but LLM summary generation will fail until a key is provided. Obtain an EPF key at <https://locallm.mde.epf.fr/>. |
| `RUN_SUMMARIES_DAEMON` | Set to `1`, `true`, `yes`, or `on` to run the summaries daemon alongside the web process. Leave empty for the normal local and Compose setup. |

For Entra mode, provide the required Entra application credentials, a registered callback URL, and a private session key as described in the table. Do not commit `.env` or publish its values. Docker Compose reads `.env` as runtime configuration; the Docker image does not need credentials baked into it.

Additional LLM providers can be configured by an administrator in the application. Their secret values belong in the environment, not in the SQLite database; the provider configuration stores the environment-variable name.

## Main areas

- Student, program-manager, facilitator, campus-manager, and administrator dashboards.
- Survey creation, enrollment, response collection, CSV export, and results visualization.
- Teacher satisfaction analytics for authorized program and campus managers.
- Optional LLM-generated summaries and administration of prompts, providers, and model prices.

The importable application package is `src/oceens/`. Its `core`, `models`, `routers`, and `services` modules contain the application logic; templates, static assets, and import data live in the same package. The SQLite database remains in the repository-level `database/` directory by default.

## Validation before contributing

Follow the [manual smoke test](docs/smoke-test.md) for the detailed startup, configuration-failure, Docker, and optional LLM checks. It is the single source of truth for validation commands; this README intentionally does not repeat them.

For behavior changes, also test the affected routes using a disposable SQLite database, relevant roles, and relevant survey states. Never use a production database copy for manual tests.

## Further reading

- [Project context and vocabulary](CONTEXT.md)
- [Architecture decision records](docs/adr/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [uv documentation](https://docs.astral.sh/uv/)
