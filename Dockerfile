FROM python:3.12-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/

ENV MCP_PORT=8000
ENV MCP_TRANSPORT=http

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "src.wordle_server.server"]
