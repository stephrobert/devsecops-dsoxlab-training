# Challenge : le pipeline minimal

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
