# Challenge : SBOM et provenance

5 tâches, 100 points, 55 minutes.

Le projet est dans `challenge/work`. Vous faites évoluer
`.github/workflows/ci.yml` et `threat-model.yml`, et vous créez
`scripts/verify_release.sh`.

### Tâche 1 : le SBOM de l'image est confronté au verrou (20 pts)

`act pull_request` est vert, et le job montre la ligne
« SBOM matches uv.lock » de l'outil de l'équipe.

### Tâche 2 : un paquet hors du verrou arrête le pipeline (20 pts)

Dans une copie dont l'image installe `six` hors de `uv.lock`, le job échoue
sur la confrontation du SBOM.

### Tâche 3 : le déploiement atteste la provenance de l'archive (20 pts)

Le job de déploiement, réservé à main, déclare `id-token: write` et
`attestations: write`, et atteste l'archive `.tgz` avec une action épinglée
par SHA.

### Tâche 4 : la vérification exige le dépôt, le workflow et main (20 pts)

`scripts/verify_release.sh <archive>` appelle `gh attestation verify` avec
le dépôt, le workflow signataire, la référence et le refus des runners
auto-hébergés, et échoue quand la vérification échoue.

### Tâche 5 : le SBOM est publié, le modèle à jour (20 pts)

Le job de déploiement publie `sbom.cdx.json` à côté de l'archive, et T-14 est
`mitigated` avec sa preuve.
