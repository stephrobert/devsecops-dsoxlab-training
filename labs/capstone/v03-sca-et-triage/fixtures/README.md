# notes-api

Un petit service de notes en Flask : chaque utilisateur range ses notes,
l'API les liste, les cherche et en crée. Un lot de notes signé en ECDSA
peut aussi être importé d'un service partenaire (`POST /notes/import`).

```bash
uv sync
uv run pytest
uv run flask --app notes_api.app:create_app run
```

Ce dépôt est le projet du fil rouge DevSecOps : chaque lab le fait évoluer.
