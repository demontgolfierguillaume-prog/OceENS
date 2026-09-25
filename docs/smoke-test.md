# Manual smoke test

The project does not yet have a complete automated test suite or CI workflow. This procedure starts the application as an external process and checks its HTTP responses and exit codes.

Run it before proposing changes to startup, configuration, dependencies, or the container. Start from a fresh clone when validating a release candidate.

## Prerequisites and shell conventions

Install [uv](https://docs.astral.sh/uv/) and Docker if running the container checks. The Python version is declared in `.python-version`; `uv` creates the project environment and installs the locked dependencies. The application can start without Entra credentials or an LLM key when using the development configuration in `.env.example`.

Commands are shown for Windows PowerShell and macOS/Linux Bash. PowerShell may block virtual-environment activation scripts by default; the examples use `uv run` and do not require activation.

## Static checks

From the repository root:

```text
uv run python -m compileall -q src/oceens
uv run python -c "import oceens"
git diff --check
```

## 1. Local startup without external credentials

In a fresh clone, create the local configuration file, install the locked dependencies, and start the application.

**Windows (PowerShell)**

```powershell
Copy-Item .env.example .env
uv sync --frozen
uv run uvicorn oceens.main:app --port 8000
```

**macOS / Linux (Bash)**

```bash
cp .env.example .env
uv sync --frozen
uv run uvicorn oceens.main:app --port 8000
```

With the development settings from `.env.example`, no Entra account or LLM key is needed. Check these routes:

| Request | Expected result |
| --- | --- |
| `GET /` | 200 |
| `GET /dev/login` | 200 |
| `GET /nope` | 303 redirect to `/` (the application redirects 404 responses) |

Startup logs should show database tables and demonstration data being initialized without errors or exception traces. Stop the server with Ctrl+C.

To check that startup is independent of the current working directory, change to a directory outside the clone and run the installed package using its project path:

**Windows (PowerShell)**

```powershell
uv run --project "C:\path\to\OceENS" python -c "import oceens"
uv run --project "C:\path\to\OceENS" uvicorn oceens.main:app --port 8001
```

**macOS / Linux (Bash)**

```bash
uv run --project "/path/to/OceENS" python -c "import oceens"
uv run --project "/path/to/OceENS" uvicorn oceens.main:app --port 8001
```

The import must succeed and the server must start using the clone's `.env`, templates, and root-level database directory. Stop it with Ctrl+C.

## 2. Docker Compose startup

Docker must be running. Docker Desktop with the WSL 2 backend is suitable on Windows; macOS and Linux need a running Docker daemon.

Ensure the root `.env` exists as described above, then run:

```text
docker compose up --build
```

The container should remain running without a restart loop. The routes `/`, `/dev/login`, and `/nope` should return the same responses as in the local check. Compose requires `.env` because it is declared as an `env_file`.

Stop with Ctrl+C, then clean up the containers:

```text
docker compose down
```

## 3. Invalid authentication configuration

Invalid startup configuration should exit with code 1. Temporarily set the environment values below only in the test shell. For the missing-Entra and missing-session-key checks, move `.env` aside so its development defaults are not loaded; restore it after the checks.

**Windows (PowerShell)**

```powershell
# Invalid authentication mode
$env:AUTH_MODE = "bogus"
uv run python -c "import oceens.main"; $LASTEXITCODE   # 1
Remove-Item Env:AUTH_MODE

# Missing Entra settings, without .env
Rename-Item .env .env.bak
'AUTH_MODE','ENTRA_CLIENT_ID','ENTRA_CLIENT_SECRET','ENTRA_TENANT_ID' |
  ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }
uv run python -c "import oceens.main"; $LASTEXITCODE   # 1

# Missing session key in Entra mode
$env:AUTH_MODE = "entra"
$env:ENTRA_CLIENT_ID = "x"; $env:ENTRA_CLIENT_SECRET = "x"; $env:ENTRA_TENANT_ID = "x"
Remove-Item Env:SECRET_KEY -ErrorAction SilentlyContinue
uv run python -c "import oceens.main"; $LASTEXITCODE   # 1
'AUTH_MODE','ENTRA_CLIENT_ID','ENTRA_CLIENT_SECRET','ENTRA_TENANT_ID' |
  ForEach-Object { Remove-Item "Env:$_" }
Rename-Item .env.bak .env
```

**macOS / Linux (Bash)**

```bash
# Invalid authentication mode
AUTH_MODE=bogus uv run python -c "import oceens.main"; echo $?   # 1

# Missing Entra settings, without .env
mv .env .env.bak
env -u AUTH_MODE -u ENTRA_CLIENT_ID -u ENTRA_CLIENT_SECRET -u ENTRA_TENANT_ID \
  uv run python -c "import oceens.main"; echo $?   # 1

# Missing session key in Entra mode
env -u SECRET_KEY AUTH_MODE=entra ENTRA_CLIENT_ID=x ENTRA_CLIENT_SECRET=x ENTRA_TENANT_ID=x \
  uv run python -c "import oceens.main"; echo $?   # 1
mv .env.bak .env
```

Expected logs identify the invalid authentication mode, missing Entra settings, or missing session key. As a control, development mode starts without a session key.

## 4. No LLM key

The example configuration leaves the default LLM key empty. The web application should still start; only LLM-generated summaries are unavailable. If the summaries daemon is running, a requested summary should be marked with a configuration error (`http_status` 500, missing or empty environment variable), and no request should be sent to the provider.

## 5. With an LLM key (optional)

Each student can obtain an individual EPF key at <https://locallm.mde.epf.fr/> and store it in their ignored `.env` file. Do not paste or commit the key.

For a direct client check, the key must be present in the command's environment. The `llm_client` module does not itself load `.env`.

**Windows (PowerShell)**

```powershell
$env:LLM_API_KEY = "<your key>"
uv run python -c "from types import SimpleNamespace; from oceens.services import llm_client as c; p = SimpleNamespace(name='Ollama EPF', api_type='ollama', base_url='https://locallm.mde.epf.fr/ollama', api_key_env='LLM_API_KEY', default_model='gemma4:26b'); print(c.check_model(p, 'gemma4:26b')); print(c.ping_generation(p, 'gemma4:26b'))"
Remove-Item Env:LLM_API_KEY
```

**macOS / Linux (Bash)**

```bash
LLM_API_KEY='<your key>' uv run python -c "from types import SimpleNamespace; from oceens.services import llm_client as c; p = SimpleNamespace(name='Ollama EPF', api_type='ollama', base_url='https://locallm.mde.epf.fr/ollama', api_key_env='LLM_API_KEY', default_model='gemma4:26b'); print(c.check_model(p, 'gemma4:26b')); print(c.ping_generation(p, 'gemma4:26b'))"
```

Expected output is `True`, followed by `(True, None, None)`. Checking the model list alone does not confirm that the provider can generate text; the ping performs a minimal generation request.

For an end-to-end check, run `uv run oceens-summaries-daemon` in a separate terminal, request summary generation for a test survey, and confirm that a summary is produced. The daemon loads `.env` at startup. Stop it after the check and remove test summaries using the application interface.

## After the smoke test

Manually test routes affected by the change using a disposable SQLite database, with relevant user roles and survey states. Never use a production database copy.
