# notes-api, image de production.
#
# Deux étapes : la première installe les dépendances VERROUILLÉES (uv.lock,
# sans le groupe dev) dans un environnement virtuel ; la seconde ne garde que
# cet environnement et le code, et tourne sous un utilisateur sans privilège.
# Images épinglées par digest, relevé le 2026-10-03.

FROM python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.21@sha256:a7aed3216253ee804de3e2d8afa5073baa1a177335345d43845cd4165e43b711 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

FROM python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
# L'image de base date de son dernier build : les correctifs Debian publiés
# depuis s'appliquent ici, à chaque construction.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin notes
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY src ./src
ENV PATH=/app/.venv/bin:$PATH PYTHONPATH=/app/src
USER 10001
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')"]
CMD ["flask", "--app", "notes_api.app:create_app", "run", "--host", "0.0.0.0"]
