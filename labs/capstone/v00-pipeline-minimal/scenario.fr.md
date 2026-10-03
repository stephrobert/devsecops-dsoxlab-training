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
