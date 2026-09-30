FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /build

# Build context is the repo root (docker-compose.yml: build.context: ..), because
# pyproject.toml resolves meadows-protocol through [tool.uv.sources] as
# ../meadows-protocol. The sibling must exist at exactly that relative path next
# to meadows-web/, so it is copied in first and installed on its own for caching.
COPY meadows-protocol/ meadows-protocol/
COPY meadows-web/pyproject.toml meadows-web/README.md meadows-web/
COPY meadows-web/src/ meadows-web/src/

RUN cd /build/meadows-protocol && uv pip install --system --no-cache . && \
    cd /build/meadows-web && uv pip install --system --no-cache .
EXPOSE 8081

# Render the template on every start: MEADOWS_SERVER_URL (and MEADOWS_SYSTEM_NAME)
# are baked into index.html by build.py, so a plain
#   docker run -p 8081:8081 -e MEADOWS_SERVER_URL=http://chat.example.com remcoboerma/meadows-web
# must pick the URL up from the container env — never from image build time.
CMD ["sh", "-c", "python -m meadows.web.build && python -m meadows.web"]
