# Challenge : secrets et SAST bloquants

5 tâches, 100 points, 50 minutes.

Le projet est dans `challenge/work`. Vous faites évoluer
`.github/workflows/ci.yml`, `src/notes_api/app.py`, `tests/test_app.py` et
`threat-model.yml`.

### Tâche 1 : les deux portes tournent et le projet passe (20 pts)

`act push` est vert, et le job montre l'analyse de secrets, l'analyse statique
et les tests.

### Tâche 2 : un secret arrête le pipeline (20 pts)

Dans une copie qui embarque un jeton GitHub, le job échoue sur l'analyse de
secrets.

### Tâche 3 : une injection SQL arrête le pipeline (20 pts)

Dans une copie qui ajoute une route concaténant une valeur dans sa requête, le
job échoue sur l'analyse statique.

### Tâche 4 : la recherche résiste à l'injection (20 pts)

`GET /notes/search?q=' OR '1'='1` ne rend aucune note.

### Tâche 5 : le modèle dit la menace traitée, et sa preuve (20 pts)

La menace d'altération de `GET /notes/search` est `mitigated`, et sa preuve est
un test de régression qui tente l'injection.
