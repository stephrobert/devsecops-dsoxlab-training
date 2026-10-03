# notes-api

Un petit service de notes en Flask : chaque utilisateur range ses notes,
l'API les liste, les cherche et en crée. Un lot de notes signé en ECDSA
peut aussi être importé d'un service partenaire (`POST /notes/import`).

```bash
uv sync
uv run pytest
uv run flask --app notes_api.app:create_app run
```

Le dépôt GitHub du projet est `acme/notes-api`, et ses versions sont publiées
dans le bucket `notes-api-releases` du compte AWS `123456789012`.

En production, notes-api tourne dans l'espace de noms `notes-api` d'un cluster
Kubernetes, et ses images viennent du registre interne
`registry.notes.internal:5000`. La plateforme y signe chaque image avec sa clé
KMS ; la clé publique correspondante est `deploy/signing/cosign.pub`.

Ce dépôt est le projet du fil rouge DevSecOps : chaque lab le fait évoluer.
