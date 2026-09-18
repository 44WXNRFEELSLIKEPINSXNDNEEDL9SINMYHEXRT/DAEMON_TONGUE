FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# HF Spaces runs containers as uid 1000; a root-owned /app makes the model
# cache unwritable at startup.
RUN useradd -m -u 1000 daemon
USER daemon
WORKDIR /home/daemon/app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    HF_HOME=/home/daemon/.cache/huggingface \
    PORT=7860

COPY --chown=daemon:daemon pyproject.toml uv.lock ./
# The lockfile pulls the CUDA build of torch, so the image is large. For a lean
# CPU image, re-resolve torch against https://download.pytorch.org/whl/cpu.
RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=daemon:daemon src/ ./src/

EXPOSE 7860

CMD ["sh", "-c", "uv run --no-sync uvicorn api:app --app-dir src --host 0.0.0.0 --port ${PORT}"]
