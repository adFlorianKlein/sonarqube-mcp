FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/

ENV MCP_HOST=0.0.0.0

EXPOSE 8070

CMD ["uv", "run", "python", "src/sonarqube_mcp/server.py"]
