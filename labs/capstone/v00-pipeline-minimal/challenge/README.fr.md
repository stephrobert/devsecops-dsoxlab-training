# V0 : un pipeline qui teste chaque changement

## Situation

L'équipe qui maintient **notes-api** livre à la main. Les tests existent, cinq
tests pytest dans `tests/`, mais rien ne les lance : un changement qui casse
la recherche de notes part en production si personne n'a pensé à les jouer.

Le répertoire `challenge/work` contient le projet tel que l'équipe vous le
confie : l'application dans `src/notes_api/`, ses tests, `pyproject.toml` et
son verrou `uv.lock`. Il porte aussi un `Dockerfile` et un dossier `infra/`
dont ce lab ne s'occupe pas : les versions suivantes du fil rouge y
reviendront. Aucun workflow.

## Objectif

Un workflow GitHub Actions qui, à chaque **push** et à chaque **pull
request** vers `main`, dans un seul job :

1. récupère le code ;
2. installe les dépendances **exactement** comme `uv.lock` les décrit ;
3. lance les tests.

Un test cassé doit rendre le pipeline rouge. Un `pyproject.toml` modifié sans
mettre à jour `uv.lock` aussi : la CI installe ce qui a été verrouillé et
relu, pas ce que l'index publie ce jour-là.

Pratique SSDF visée : PO.3 (mettre en place la chaîne d'outils qui automatise les contrôles).

## Repères

- GitHub ne lit les workflows que dans `.github/workflows/`.
- `astral-sh/setup-uv` installe uv ; `uv sync --locked` refuse un verrou qui
  ne correspond plus à `pyproject.toml`.
- `act -l` liste ce qu'act a compris de vos fichiers ; `act push` et
  `act pull_request` jouent le workflow.

## Vérifier

```bash
dsoxlab check capstone-v00-pipeline-minimal
```

Cinq contrôles, vingt points chacun. Ils jouent votre workflow avec act sur
le projet, puis sur des copies cassées exprès : un test qui ne passe plus, un
verrou désynchronisé, une pull request. Docker doit répondre (`docker info`).

## Le pipeline minimal

5 tâches, 100 points, 30 minutes.

Le projet est dans `challenge/work`. Tout se passe dans
`.github/workflows/`, que vous créez. Les tests jouent votre workflow avec act
et lisent ce qu'il produit ; ils ne lisent pas vos commandes.

### Tâche 1 : le code livré passe (20 pts)

`act push` joue un seul job, vert, sur le projet tel qu'il est.

### Tâche 2 : les tests tournent dans le pipeline (20 pts)

Le job montre pytest collectant `tests/test_app.py` et rendant son bilan.

### Tâche 3 : un test cassé rend le pipeline rouge (20 pts)

Dans une copie où `/health` ne répond plus `ok`, le job échoue.

### Tâche 4 : un verrou désynchronisé rend le pipeline rouge (20 pts)

Dans une copie où `pyproject.toml` déclare une dépendance absente de
`uv.lock`, le job refuse d'installer.

### Tâche 5 : les pull requests passent le même contrôle (20 pts)

`act pull_request` joue le même job, vert, tests compris.
