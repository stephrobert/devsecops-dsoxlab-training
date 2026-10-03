# Challenge : l'image et l'infrastructure

5 tâches, 100 points, 60 minutes.

Le projet est dans `challenge/work`. Vous faites évoluer
`.github/workflows/ci.yml`, `Dockerfile`, `infra/main.tf`, `infra/deploy.tf`
et `threat-model.yml`.

### Tâche 1 : l'image et l'infrastructure sont analysées, le projet passe (20 pts)

`act pull_request` est vert, et le job montre Trivy analysant la
configuration puis l'image construite.

### Tâche 2 : un Dockerfile sans utilisateur arrête le pipeline (20 pts)

Dans une copie dont le Dockerfile n'a plus de `USER`, le job échoue sur la
règle DS-0002.

### Tâche 3 : un SSH ouvert au monde arrête le pipeline (20 pts)

Dans une copie qui ajoute un security group ouvrant le port 22 à
`0.0.0.0/0`, le job échoue sur la règle AWS-0107.

### Tâche 4 : l'image tourne sans privilège, avec le verrou (20 pts)

Les images de base sont épinglées par digest, l'image s'exécute sous un uid
non nul, embarque les versions de `uv.lock` et n'embarque pas pytest.

### Tâche 5 : le modèle dit l'image et l'infrastructure traitées (20 pts)

Aucune règle d'entrée n'accepte `0.0.0.0/0`, et T-09 et T-10 sont
`mitigated` avec leur preuve.
