FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Ensure installed tools can be executed out of the box
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project


COPY . .

RUN uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000
EXPOSE 5100

ENTRYPOINT [ ]

CMD [ "uv", "run", "server.py" ]