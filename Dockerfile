FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.2 /uv /uvx /bin/

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOCAL_DATABASE_DIR=/app/database \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock .python-version ./
COPY src ./src

RUN uv sync --frozen --no-dev --no-editable

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "oceens-server"]
